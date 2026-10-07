"""Contract folder scan: finds and PROPOSES contract entries. All documents here are invented."""
import sys
import zipfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import contract_scan as cs  # noqa: E402


def docx(path, *paragraphs):
    body = "".join(f"<w:p><w:r><w:t xml:space=\"preserve\">{p}</w:t></w:r></w:p>" for p in paragraphs)
    with zipfile.ZipFile(path, "w") as z:
        z.writestr("word/document.xml", f'<?xml version="1.0"?><w:document xmlns:w="x"><w:body>{body}</w:body></w:document>')
    return path


def test_contract_numbers_with_and_without_prefixes_and_hyphens():
    text = "Contract No. FA8650-12-D-1234 and 123456-12-D-1234, also W56HZV19C0014, order FA8650-12-D-1234-0005."
    nums = cs.find_contract_numbers(text)
    assert "FA8650-12-D-1234" in nums and "123456-12-D-1234" in nums and "W56HZV-19-C-0014" in nums
    assert "FA8650-12-D-1234-0005" not in nums            # an order under a contract belongs to that contract
    assert cs.base_number("FA8650-12-D-1234-0005") == "FA8650-12-D-1234"


def test_ordinary_numbers_are_not_contracts():
    text = "Call 505-259-8485 on 2026-10-07, invoice 20230401-A, page 12-34-56, ISBN 123456-78-9."
    assert cs.find_contract_numbers(text) == []


def test_gsa_schedule_and_order_numbers():
    nums = cs.find_contract_numbers("GSA Schedule GS-35F-0119Y and order 47QTCA19D0012.")
    assert "GS-35F-0119Y" in nums and "47QTCA-19-D-0012" in nums            # same shape as any contract number: normalised alike


def test_clauses_are_found_normalised_and_the_relevant_ones_flagged():
    text = "FAR 52.204-21 applies. See DFARS 252.204-7012, 252.204-7019 and DFARS 252.204-7021. Also FAR 52.219-8."
    cl = cs.find_clauses(text)
    assert {"FAR 52.204-21", "DFARS 252.204-7012", "DFARS 252.204-7019", "DFARS 252.204-7021"} <= set(cl)
    assert cs.RELEVANT["DFARS 252.204-7012"]["information"] == "CUI"
    assert cs.RELEVANT["FAR 52.204-21"]["information"] == "FCI"
    assert "FAR 52.219-8" in cl and "FAR 52.219-8" not in cs.RELEVANT


def test_markers_and_revision_hints():
    text = "Handle Controlled Unclassified Information (CUI) per NIST SP 800-171 Revision 3. ITAR applies. Sign the non-disclosure agreement."
    m = cs.find_markers(text)
    assert {"CUI", "ITAR", "NDA"} <= m and "FCI" not in m
    assert cs.find_revision_hints("NIST SP 800-171 Rev. 2 and Revision 3") == {"2", "3"}
    assert cs.find_revision_hints("no mention") == set()


def test_information_type_follows_the_highest_level():
    assert cs.information_type({"CUI"}, []) == "CUI"
    assert cs.information_type({"FCI"}, []) == "FCI"
    assert cs.information_type(set(), ["DFARS 252.204-7012"]) == "CUI"
    assert cs.information_type({"FCI"}, ["DFARS 252.204-7012"]) == "CUI"        # highest wins
    assert cs.information_type(set(), ["FAR 52.204-21"]) == "FCI"
    assert cs.information_type(set(), []) == "unknown"


def test_agency_group_is_only_guessed_from_well_known_prefixes():
    assert cs.agency_guess("FA8650-12-D-1234") == "DoW"
    assert cs.agency_guess("W56HZV-19-C-0014") == "DoW"
    assert cs.agency_guess("47QTCA-19-D-0012") == "GSA"
    assert cs.agency_guess("123456-12-D-1234") == "unknown"                      # no basis: say so


def test_scan_groups_documents_by_contract_and_keeps_orders_with_the_base(tmp_path):
    docx(tmp_path / "base.docx", "PRIME CONTRACT FA8650-12-D-1234", "FAR 52.204-21", "DFARS 252.204-7012")
    docx(tmp_path / "order5.docx", "Delivery Order FA8650-12-D-1234-0005", "CUI marking required")
    props = cs.scan_folder(tmp_path)
    prime = [p for p in props if p["reference"] == "FA8650-12-D-1234"]
    assert len(prime) == 1 and set(prime[0]["files"]) == {"base.docx", "order5.docx"}
    assert prime[0]["information"] == "CUI" and prime[0]["agency_group"] == "DoW"
    assert prime[0]["confidence"] == "high"


def test_a_subcontract_without_a_prime_number_gets_its_own_entry_and_a_kind(tmp_path):
    (tmp_path / "sub.md").write_text("# Subcontract Agreement\nThis subcontract flows down FAR 52.204-21.\nPrime contract number: not provided.\n")
    (tmp_path / "po.txt").write_text("PURCHASE ORDER\nSupplier shall comply with DFARS 252.204-7012.\n")
    props = {p["files"][0]: p for p in cs.scan_folder(tmp_path)}
    assert props["sub.md"]["instrument"] == "subcontract" and props["sub.md"]["reference"] == ""
    assert props["sub.md"]["information"] == "FCI" and props["sub.md"]["prime_known"] == "no"
    assert props["po.txt"]["instrument"] == "purchase_order" and props["po.txt"]["information"] == "CUI"


def test_a_standalone_nda_is_recognised(tmp_path):
    (tmp_path / "nda.txt").write_text("MUTUAL NON-DISCLOSURE AGREEMENT between the parties. Proprietary information shall be protected.")
    p = cs.scan_folder(tmp_path)[0]
    assert p["instrument"] == "nda" and p["duty_from"] == "nda"


def test_unreadable_files_are_listed_for_a_person_not_guessed(tmp_path):
    (tmp_path / "scan.png").write_bytes(b"\x89PNG not text")
    (tmp_path / "broken.docx").write_bytes(b"not a zip")
    props = {p["files"][0]: p for p in cs.scan_folder(tmp_path)}
    assert props["scan.png"]["needs_a_person"] and props["broken.docx"]["needs_a_person"]
    assert props["scan.png"]["information"] == "unknown"


def test_the_ini_proposal_is_marked_unconfirmed_and_never_contains_document_text(tmp_path):
    docx(tmp_path / "base.docx", "PRIME CONTRACT FA8650-12-D-1234", "The secret sauce recipe is confidential.", "DFARS 252.204-7012")
    ini = cs.proposals_to_ini(cs.scan_folder(tmp_path))
    assert "[contract.1]" in ini and "FA8650-12-D-1234" in ini and "information = CUI" in ini
    assert "PROPOSED" in ini and "confirm" in ini.lower()
    assert "secret sauce" not in ini
    import configparser
    c = configparser.ConfigParser(inline_comment_prefixes=(";",), interpolation=None)
    c.read_string(ini)
    assert c["contract.1"]["information"] == "CUI"


# ---- found by a first trial on real documents
def test_government_award_forms_are_prime_contracts_even_when_they_say_purchase_order():
    form = "SOLICITATION/CONTRACT/ORDER FOR COMMERCIAL PRODUCTS AND COMMERCIAL SERVICES  STANDARD FORM 1449  Contract/Purchase Order No. W56HZV-19-C-0014"
    assert cs.instrument_guess(form) == "prime"
    assert cs.instrument_guess("AWARD/CONTRACT  1. THIS CONTRACT IS A RATED ORDER  Standard Form 26") == "prime"
    assert cs.instrument_guess("PURCHASE ORDER 77 issued by Acme Corp to Supplier") == "purchase_order"
    # the form's name can sit well down the first page
    assert cs.instrument_guess(("x " * 500) + "STANDARD FORM 1449") == "prime"


def test_a_modification_form_belongs_to_its_contract():
    assert cs.instrument_guess("AMENDMENT OF SOLICITATION/MODIFICATION OF CONTRACT  Standard Form 30") == "modification"


def test_agency_supplement_clauses_are_found_and_named():
    text = "NFS 1852.204-76 and AFFARS 5352.201-9101, GSAR 552.239-71, HSAR 3052.204-71, FAR 52.204-21"
    cl = cs.find_clauses(text)
    assert {"NFS 1852.204-76", "AFFARS 5352.201-9101", "GSAR 552.239-71", "HSAR 3052.204-71", "FAR 52.204-21"} <= set(cl)
    assert "FAR 52.204-76" not in cl and "FAR 52.239-71" not in cl                 # a longer prefix is not a FAR clause


def test_an_agency_security_clause_is_a_duty_even_when_it_names_no_level():
    assert "NFS 1852.204-76" in cs.RELEVANT and cs.RELEVANT["NFS 1852.204-76"]["information"] is None
    assert cs.information_type(set(), ["NFS 1852.204-76"]) == "unknown"            # the clause does not say CUI or FCI


def test_a_proposal_is_only_high_confidence_when_the_level_is_known(tmp_path):
    (tmp_path / "nasa.txt").write_text("AWARD/CONTRACT 80NSSC-20-C-0010\nNFS 1852.204-76 applies.\n")
    (tmp_path / "army.txt").write_text("AWARD/CONTRACT W56HZV-19-C-0014\nDFARS 252.204-7012 applies.\n")
    props = {p["files"][0]: p for p in cs.scan_folder(tmp_path)}
    assert props["nasa.txt"]["confidence"] == "medium" and props["nasa.txt"]["duty_from"] == "clauses"
    assert props["army.txt"]["confidence"] == "high" and props["army.txt"]["instrument"] == "prime"


# ---- found by the second look at real documents: the letter in the number says what it is
def test_the_type_letter_in_a_contract_number_says_what_it_is():
    assert cs.number_kind("FA9453-19-C-0500") == "award"
    assert cs.number_kind("W81XWH-20-R-0124") == "solicitation"          # request for proposals
    assert cs.number_kind("W81XWH-20-Q-0080") == "solicitation"          # request for quotations
    assert cs.number_kind("N68335-19-G-0041") == "agreement"             # basic ordering agreement
    assert cs.number_kind("FA8650-12-D-1234") == "award"                 # indefinite-delivery contract
    assert cs.number_kind("FA8650-12-F-0005") == "order"
    assert cs.number_kind("GS-35F-0119Y") == "award"
    assert cs.number_kind("ABCDEF-12-Z-1234") == "unknown"


def test_civilian_agency_codes_in_the_first_two_characters():
    assert cs.agency_guess("80GSFC-20-C-0010") == "other_civilian"       # NASA
    assert cs.agency_guess("70RSAT-21-C-0001") == "other_civilian"       # DHS
    assert cs.agency_guess("47QTCA-19-D-0012") == "GSA"
    assert cs.agency_guess("FA8650-12-D-1234") == "DoW"


def test_a_solicitation_is_not_proposed_as_a_contract_and_an_award_without_a_form_title_is_prime(tmp_path):
    (tmp_path / "rfp.txt").write_text("Conformed solicitation W81XWH-20-R-0124 includes DFARS 252.204-7012.")
    (tmp_path / "award.txt").write_text("Full text of FA9453-19-C-0500 with DFARS 252.204-7012.")
    props = {p["files"][0]: p for p in cs.scan_folder(tmp_path)}
    assert props["rfp.txt"]["instrument"] == "solicitation" and props["rfp.txt"]["number_kind"] == "solicitation"
    assert props["award.txt"]["instrument"] == "prime" and props["award.txt"]["number_kind"] == "award"
    ini = cs.proposals_to_ini(list(props.values()))
    assert "SOLICITATION" in ini                                          # said plainly in the proposal


# ---- the structure of a PIIN (owner, 2026-10-07): funding office - fiscal year - type letter - sequence, hyphens often removed
def test_a_piin_decodes_into_office_year_type_and_sequence():
    d = cs.decode_piin("A12345-00-C-1234")
    assert d == {"office": "A12345", "fiscal_year": 2000, "type_letter": "C", "kind": "award", "sequence": "1234"}
    assert cs.decode_piin("W81XWH-20-R-0124")["fiscal_year"] == 2020
    assert cs.decode_piin("FA8650-98-D-0001")["fiscal_year"] == 1998          # two digits: 50 and above read as the 1900s
    assert cs.decode_piin("GS-35F-0119Y") is None                              # a schedule number has a different structure


def test_the_same_piin_with_hyphens_removed_reads_identically():
    assert cs.find_contract_numbers("W81XWH20R0124") == cs.find_contract_numbers("W81XWH-20-R-0124") == ["W81XWH-20-R-0124"]
    assert cs.find_contract_numbers("A12345-00-C-1234") == ["A12345-00-C-1234"]


def test_proposals_carry_the_fiscal_year_and_say_it_in_plain_words(tmp_path):
    (tmp_path / "old.txt").write_text("Conformed solicitation W56HZV-15-R-0026 with DFARS 252.204-7012.")
    p = cs.scan_folder(tmp_path)[0]
    assert p["fiscal_year"] == 2015 and p["office"] == "W56HZV"
    assert "FY2015" in cs.proposals_to_ini([p])


# ---- owner's context (2026-10-07): a duty in a clause is not the same as marked CUI; a solicitation previews its award
def test_marked_cui_is_told_apart_from_the_word_cui_in_clause_text():
    assert cs.find_cui_marking("CUI\nThis document\nCUI", "plain.pdf")["marked"]                      # banner lines
    assert cs.find_cui_marking("(CUI) The contractor shall deliver.\n(CUI) Reports are due monthly.", "plain.pdf")["marked"]   # portion markings
    assert cs.find_cui_marking("Controlled by: Army\nCUI Category: CTI\nPOC: office", "plain.pdf")["marked"]   # designation indicator
    assert cs.find_cui_marking("nothing special", "CUI Statement of Work.docx")["marked"]            # filename prefix
    assert not cs.find_cui_marking("The contractor shall protect CUI in accordance with DFARS 252.204-7012.", "contract.pdf")["marked"]


def test_categories_and_dissemination_controls_come_from_the_marking():
    m = cs.find_cui_marking("CUI//SP-CTI//NOFORN\nbody\nCUI//SP-CTI//NOFORN", "x.pdf")
    assert m["marked"] and m["categories"] == ["CTI"] and m["dissemination"] == ["NOFORN"]
    d = cs.find_cui_marking("Controlled by: DLA\nCUI Category: EXPT, CTI\nLimited Dissemination Control: FEDCON\nPOC: x", "x.pdf")
    assert d["categories"] == ["CTI", "EXPT"] and d["dissemination"] == ["FEDCON"]
    assert cs.find_cui_marking("no marking here", "x.pdf") == {"marked": False, "categories": [], "dissemination": [], "how": []}


def test_a_solicitation_previews_its_award_so_the_duty_is_if_awarded_not_now(tmp_path):
    (tmp_path / "rfp.txt").write_text("Solicitation W81XWH-20-R-0124. SECTION K - REPRESENTATIONS. SECTION L - INSTRUCTIONS. SECTION M - EVALUATION. DFARS 252.204-7012 applies.")
    p = cs.scan_folder(tmp_path)[0]
    assert p["instrument"] == "solicitation"
    assert p["information_if_awarded"] == "CUI" and p["information"] == "unknown"      # nothing in the document itself is marked
    assert p["cui_marked"] is False


def test_sections_k_l_m_mark_a_solicitation_even_when_the_number_says_contract(tmp_path):
    (tmp_path / "conformed.txt").write_text("STANDARD FORM 1449 W56HZV-19-C-0014\nSECTION K - REPRESENTATIONS AND CERTIFICATIONS\nSECTION L - INSTRUCTIONS TO OFFERORS\nSECTION M - EVALUATION FACTORS FOR AWARD\n")
    assert cs.scan_folder(tmp_path)[0]["instrument"] == "solicitation"


def test_a_marked_cui_attachment_joins_the_contract_kept_in_the_same_subfolder(tmp_path):
    d = tmp_path / "Contract A"
    d.mkdir()
    (d / "Award.txt").write_text("AWARD/CONTRACT FA9453-19-C-0500 with DFARS 252.204-7012.")
    (d / "CUI Statement of Work.txt").write_text("CUI//SP-CTI\nThe work is described here.\nCUI//SP-CTI")
    (tmp_path / "Other.txt").write_text("AWARD/CONTRACT FA8650-12-D-1234")
    props = {p["reference"]: p for p in cs.scan_folder(tmp_path)}
    a = props["FA9453-19-C-0500"]
    assert len(a["files"]) == 2 and a["cui_marked"] is True and a["categories"] == ["CTI"]
    assert any("CUI Statement of Work" in f for f in a["joined_by_folder"])
    assert len(props["FA8650-12-D-1234"]["files"]) == 1


def test_a_loose_attachment_in_a_flat_folder_with_several_contracts_is_not_guessed_onto_one(tmp_path):
    (tmp_path / "A.txt").write_text("AWARD/CONTRACT FA9453-19-C-0500")
    (tmp_path / "B.txt").write_text("AWARD/CONTRACT FA8650-12-D-1234")
    (tmp_path / "CUI SOW.txt").write_text("CUI\nwork\nCUI")
    props = cs.scan_folder(tmp_path)
    sow = next(p for p in props if "CUI SOW.txt" in p["files"])
    assert sow["reference"] == "" and sow["cui_marked"] is True


def test_the_proposal_shows_marking_separately_from_the_duty(tmp_path):
    (tmp_path / "award.txt").write_text("CUI//SP-EXPT//NOFORN\nAWARD/CONTRACT FA9453-19-C-0500 DFARS 252.204-7012\nbody\nCUI//SP-EXPT//NOFORN")
    ini = cs.proposals_to_ini(cs.scan_folder(tmp_path))
    assert "cui_marked = yes" in ini and "cui_categories = EXPT" in ini and "dissemination_controls = NOFORN" in ini


def test_defining_the_abbreviation_is_not_marking_and_a_single_stray_mark_is_not_enough():
    defined = "Controlled Unclassified Information (CUI) means... as described in the controlled unclassified information (CUI) Registry. See also Controlled Unclassified Information (CUI) here."
    assert not cs.find_cui_marking(defined, "contract.pdf")["marked"]
    assert not cs.find_cui_marking("(CUI) one stray mark only", "contract.pdf")["marked"]            # real markings repeat
    assert not cs.find_cui_marking("a list item\nCUI\nanother item", "contract.pdf")["marked"]      # one lone line is not a banner


# ---- owner's FCI reasoning (2026-10-07): a solicitation is public; an executed contract is not (prices, delivery dates)
def test_an_executed_award_carries_at_least_fci_even_when_no_clause_says_so(tmp_path):
    (tmp_path / "nasa.txt").write_text("AWARD/CONTRACT 80GSFC-20-C-0010\nNFS 1852.204-76 applies.\n")
    (tmp_path / "army.txt").write_text("AWARD/CONTRACT W56HZV-19-C-0014\nDFARS 252.204-7012 applies.\n")
    props = {p["files"][0]: p for p in cs.scan_folder(tmp_path)}
    assert props["nasa.txt"]["information"] == "FCI" and props["nasa.txt"]["information_basis"] == "award floor"
    assert props["army.txt"]["information"] == "CUI" and props["army.txt"]["information_basis"] == "clauses"


def test_a_solicitation_is_public_so_nothing_applies_now_and_an_award_would_carry_at_least_fci(tmp_path):
    (tmp_path / "rfp.txt").write_text("Solicitation W81XWH-20-R-0124 with no cybersecurity clause at all.")
    p = cs.scan_folder(tmp_path)[0]
    assert p["instrument"] == "solicitation" and p["information"] == "unknown"
    assert p["information_if_awarded"] == "FCI"


def test_the_organisation_level_counts_contracts_held_not_solicitations_bid_on(tmp_path):
    (tmp_path / "rfp.txt").write_text("Solicitation W81XWH-20-R-0124 with DFARS 252.204-7012.")
    only_bid = cs.organization_level(cs.scan_folder(tmp_path))
    assert only_bid == {"level": "unknown", "held": 0, "bids": 1, "if_all_awarded": "CUI"}
    (tmp_path / "award.txt").write_text("AWARD/CONTRACT 80GSFC-20-C-0010 NFS 1852.204-76")
    held = cs.organization_level(cs.scan_folder(tmp_path))
    assert held["level"] == "FCI" and held["held"] == 1 and held["bids"] == 1 and held["if_all_awarded"] == "CUI"
    (tmp_path / "army.txt").write_text("AWARD/CONTRACT FA9453-19-C-0500 DFARS 252.204-7012")
    assert cs.organization_level(cs.scan_folder(tmp_path))["level"] == "CUI"                  # the highest held wins


def test_the_basis_for_an_information_level_is_stated_in_the_proposal(tmp_path):
    (tmp_path / "nasa.txt").write_text("AWARD/CONTRACT 80GSFC-20-C-0010")
    ini = cs.proposals_to_ini(cs.scan_folder(tmp_path))
    assert "information = FCI" in ini and "award floor" in ini
    import configparser
    c = configparser.ConfigParser(inline_comment_prefixes=(";",), interpolation=None)
    c.read_string(ini)
    assert c["contract.1"]["information"] == "FCI"


# ---- DoD's own uses of three letters (DFARS 204.1603, as reported; the owner verifies against the regulation)
def test_the_dod_specific_type_letters():
    assert cs.number_kind("FA8650-12-S-0001") == "solicitation"     # broad agency announcement / commercial solutions opening
    assert cs.number_kind("FA8650-12-T-0001") == "solicitation"     # automated request for quotations
    assert cs.number_kind("FA8650-12-M-0001") == "order"            # FedMall purchase or delivery order


# ---- the DATE of a clause (and any class deviation noted with it) is what fixes which rules apply
def test_a_clause_date_is_read_from_beside_its_number():
    text = ("252.204-7012 Safeguarding Covered Defense Information and Cyber Incident Reporting. (MAY 2024)\n"
            "52.204-21 Basic Safeguarding of Covered Contractor Information Systems. (NOV 2021)\n")
    d = cs.find_clause_dates(text)
    assert d["DFARS 252.204-7012"] == ["MAY 2024"] and d["FAR 52.204-21"] == ["NOV 2021"]


def test_a_date_belongs_to_the_clause_before_it_not_the_next_one():
    text = "252.204-7012 Safeguarding Covered Defense Information. 252.204-7008 Compliance with Safeguarding. (OCT 2016)"
    d = cs.find_clause_dates(text)
    assert "DFARS 252.204-7012" not in d and d["DFARS 252.204-7008"] == ["OCT 2016"]


def test_one_clause_with_two_dates_lists_both_oldest_first():
    text = "52.204-21 Basic Safeguarding. (NOV 2021)\n...later attachment...\n52.204-21 Basic Safeguarding. (JUN 2016)\n"
    assert cs.find_clause_dates(text)["FAR 52.204-21"] == ["JUN 2016", "NOV 2021"]


def test_a_class_deviation_noted_with_a_clause_is_captured():
    text = "252.204-7012 Safeguarding Covered Defense Information. (DEVIATION 2024-O0013)(MAY 2024)"
    assert cs.find_clause_deviations(text)["DFARS 252.204-7012"] == ["2024-O0013"]
    assert cs.find_clause_dates(text)["DFARS 252.204-7012"] == ["MAY 2024"]
    assert cs.find_clause_deviations("252.204-7012 Safeguarding. (MAY 2024)") == {}


def test_a_mention_without_a_date_has_no_date():
    assert cs.find_clause_dates("The contractor shall comply with DFARS 252.204-7012.") == {}


def test_proposals_show_the_clause_with_its_date_and_deviation(tmp_path):
    (tmp_path / "award.txt").write_text("AWARD/CONTRACT FA9453-19-C-0500\n252.204-7012 Safeguarding Covered Defense Information. (DEVIATION 2024-O0013)(MAY 2024)\n52.204-21 Basic Safeguarding. (NOV 2021)\n")
    p = cs.scan_folder(tmp_path)[0]
    assert p["clause_dates"] == {"DFARS 252.204-7012": ["MAY 2024"], "FAR 52.204-21": ["NOV 2021"]}
    assert p["clause_deviations"] == {"DFARS 252.204-7012": ["2024-O0013"]}
    ini = cs.proposals_to_ini([p])
    assert "DFARS 252.204-7012 (MAY 2024)" in ini and "FAR 52.204-21 (NOV 2021)" in ini and "2024-O0013" in ini
    import configparser
    c = configparser.ConfigParser(inline_comment_prefixes=(";",), interpolation=None)
    c.read_string(ini)
    assert "DFARS 252.204-7012 (MAY 2024)" in c["contract.1"]["clauses"]


# ---- clause-date layouts seen in real contracts (public records tested 2026-10-07)
def test_clause_dates_in_every_layout_real_contracts_use():
    bare = "252.204-7012 Safeguarding Covered Defense Information and Cyber Incident Reporting DEC 2019 252.204-7015 Notice of Authorized Disclosure"
    assert cs.find_clause_dates(bare)["DFARS 252.204-7012"] == ["DEC 2019"]
    slash = "252.204-7012 SAFEGUARDING COVERED DEFENSE INFORMATION AND CYBER INCIDENT REPORTING OCT/2016 45 252.204-7015 NOTICE OF AUTHORIZED DISCLOSURE"
    assert cs.find_clause_dates(slash)["DFARS 252.204-7012"] == ["OCT 2016"]            # a page or row number after the date is ignored
    assert cs.find_clause_dates("52.204-21 BASIC SAFEGUARDING OF COVERED CONTRACTOR INFORMATION SYSTEMS JUN/2016 (a) Definitions.")["FAR 52.204-21"] == ["JUN 2016"]
    assert cs.find_clause_dates("252.204-7008 Compliance With Safeguarding Covered Defense Information Controls (OCT 2016)")["DFARS 252.204-7008"] == ["OCT 2016"]
    assert cs.find_clause_dates("252.204-7012 Safeguarding Covered Defense Information. (MAY/2024)")["DFARS 252.204-7012"] == ["MAY 2024"]


def test_a_date_in_a_nearby_sentence_is_not_a_clause_date():
    sentence = ("The contractor shall comply with DFARS 252.204-7012. This applies to all information systems that process, store or transmit "
                "covered defense information, and the contracting officer reviewed the plan in March 2024 before award.")
    assert cs.find_clause_dates(sentence) == {}
    assert cs.find_clause_dates("As required by 252.204-7012, the report was issued on OCT 2016 in a separate memo about something else entirely, "
                                "which is long enough that it cannot be the title of the clause.") == {}


def test_two_clauses_in_one_table_each_get_their_own_date():
    table = ("252.204-7008 Compliance With Safeguarding Covered Defense Information Controls OCT 2016 252.204-7012 Safeguarding Covered "
             "Defense Information and Cyber Incident Reporting DEC 2019 252.204-7015 Notice of Authorized Disclosure")
    d = cs.find_clause_dates(table)
    assert d["DFARS 252.204-7008"] == ["OCT 2016"] and d["DFARS 252.204-7012"] == ["DEC 2019"] and "DFARS 252.204-7015" not in d


# ---- export-controlled terms bring extra obligations beyond 800-171 (owner, 2026-10-07)
def test_export_control_terms_trigger_the_dd_form_2345_item(tmp_path):
    (tmp_path / "po.txt").write_text("PURCHASE ORDER 77. Supplier shall comply with ITAR and the EAR. Export-controlled technical data may be exchanged.")
    p = cs.scan_folder(tmp_path)[0]
    assert [r["id"] for r in p["additional_requirements"]] == ["dd_form_2345"]
    assert "DD Form 2345" in p["additional_requirements"][0]["text"]
    ini = cs.proposals_to_ini([p])
    assert "dd_form_2345 = unknown" in ini and "DD Form 2345" in ini


def test_no_export_control_terms_no_extra_items(tmp_path):
    (tmp_path / "award.txt").write_text("AWARD/CONTRACT FA9453-19-C-0500 DFARS 252.204-7012")
    p = cs.scan_folder(tmp_path)[0]
    assert p["additional_requirements"] == []
    assert "dd_form_2345" not in cs.proposals_to_ini([p])


def test_the_extra_requirements_are_reviewable_data_one_item_per_id_even_if_both_regimes_appear():
    assert cs.ADDITIONAL_REQUIREMENTS["ITAR"][0]["id"] == "dd_form_2345" and cs.ADDITIONAL_REQUIREMENTS["EAR"][0]["id"] == "dd_form_2345"
    assert [r["id"] for r in cs.additional_requirements({"ITAR", "EAR"})] == ["dd_form_2345"]      # listed once
    assert cs.additional_requirements({"CUI", "NDA"}) == []


def test_export_control_terms_do_not_silently_raise_the_level(tmp_path):
    # commercial terms that mention ITAR/EAR are not proof the data held is export controlled: the owner confirms
    (tmp_path / "po.txt").write_text("PURCHASE ORDER 77. Comply with ITAR and EAR.")
    assert cs.scan_folder(tmp_path)[0]["information"] == "unknown"

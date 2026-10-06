# Design note: the organization profile (draft for comment)

**Status:** draft, not built. The example file is [`profile.example.ini`](profile.example.ini).

## Why a profile

NIST SP 800-171 does not get easier for a small company: the same requirements apply to a one-person firm and a
large one. What changes is **how** each requirement is met, **what evidence** exists, and **which objectives truly do
not apply**. Today the assessor quietly assumes one world (a single administrator, one server). A profile makes the
assumptions explicit, so the tool can say "assessed as a three-person company" and a reader can check the facts.

**Positioning.** This is a **reference system for research and development**, not a production assessment service. It shows
how a local AI can assess a small environment safely, and it is meant to be copied and adapted.

**Scope.** This project is for very small businesses: under 20 employees, using the size categories of the article cited below
(**nano**: fewer than 5; **micro**: 5 to 9; **mini**: 10 to 19). A company of one is a nano business, the most common kind. Larger organizations (many systems,
sampling, role-based interviews) are deliberately out of scope for now. The profile is meant to stay small enough for
an owner to fill in once, in about twenty minutes.

## Who this is for: the data

The size categories and numbers below come from the peer-reviewed article D. E. Shannon, "Technical Ways to Lower Cybersecurity Costs for Small
Businesses", *Journal of Contract Management*, Vol. 18 (2023-2024), pp. 5-21 (Table 2 draws on the Federal Procurement
Data System and the U.S. Department of Labor). They describe the **small businesses that contract with the Department of
Defense**; civilian-agency contractors are not covered.

| Category | Employees per firm | Firms | Share of firms | Total employees | Average employees |
|---|---|---|---|---|---|
| Nano | fewer than 5 | 4,928 | 53% | 7,685 | 1.6 |
| Micro | 5 to 9 | 1,345 | 14% | 8,826 | 6.6 |
| Mini | 10 to 19 | 952 | 10% | 12,836 | 13.5 |
| Midi | 20 to 99 | 1,126 | 12% | 45,400 | 40.3 |
| Small | 100 to 499 | 457 | 5% | 68,935 | 151 |
| Big small | 500 or more | 528 | 6% | 367,947 | 696 |
| **Total** | | **9,336** | 100% | **511,629** | 55* |

\* Computed from the totals (511,629 / 9,336). The article's printed table gives 45 for the total row; every other row's
average matches its own totals.

**77% of these firms have fewer than 20 employees** (the article's definition of a *very small business*), and the typical
nano firm has fewer than two. So the most common company this tool serves is one where the owner is also the
administrator and the security lead; the profile should make that easy to say, and the assessor should treat it as normal,
not as a defect.

The article also gives the economics: average revenue of about $347,000 for 1 to 4 employees, $1.08 million for 5 to 9 and
$2.16 million for 10 to 19, against estimated compliance costs of $35,000 or more at the start, about $20,000 for a third-party
assessment every three years, and $150 to $200 per employee per month to maintain (2023 estimates). Those figures are why
cost is a design goal here: the article estimated that open templates and AI could remove about $10,000 of the initial cost.

### How to read these numbers

**What the data covers.** Prime contractors to the Department of Defense and the defense industrial base, in 2023-era data.
It does not include subcontracts, and it does not include civilian agencies. "Employees" is not the same as "people who use
the systems".

**The author's context** (judgment from 35 years of experience in government contracting; **not measured**):

- The figures are *directionally correct* for government contracts as a whole.
- This class of business has a **more pronounced presence in subcontracts**, which the article did not count, so very small
  firms are probably under-represented in the table.
- The **nano class is probably better represented among civilian agencies** (conjecture). Civilian agencies tend to buy
  smaller-value procurements and make set-asides for local small businesses more often.

Treat the table as the best published picture, and the context as a reasoned expectation about what is missing from it. The
profile is built so this can be checked rather than assumed: every contract records its agency group (`agency_group`)
and whether it is a prime contract or a subcontract (`vehicle`), so the real mix among the people who use this tool can
be counted if anyone ever wants to. Sharing anonymous counts is possible later but not planned (see Out of scope).

## The national picture (Census) and why it matters now

**Nationally**, the very small business is the normal business. From the U.S. Census Bureau's Statistics of U.S.
Businesses (SUSB), 2021, national table "Number of Firms and Establishments", employer firms by enterprise size
(source: 2021 County Business Patterns):

| Category (article's definitions) | Employer firms | Share |
|---|---|---|
| Nano (fewer than 5 employees) | 4,009,508 | 63.7% |
| Micro (5 to 9) | 1,021,829 | 16.2% |
| Mini (10 to 19) | 636,541 | 10.1% |
| 20 or more | 626,726 | 10.0% |
| **All employer firms** | **6,294,604** | 100% |

**Fewer than 10 employees: 79.9% (nearly 8 in 10). Fewer than 20: 90.0% (9 in 10).** These count firms with
paid employees only; the many millions of businesses with no employees at all are not in this table.

Set beside the article's DoD figures (53% nano, 14% micro, 10% mini; 77% under 20), defense contractors are somewhat
**less** concentrated in the smallest sizes than firms nationally, which is consistent with the article's concern that
cost keeps very small firms out of the defense industrial base. (Different populations: all employer firms, versus
small businesses that hold DoD prime contracts.)

**The recent CMMC pause.** On 13 July 2026 the Department of War paused Phase 2 of CMMC, the requirement for a
third-party Level 2 certification as a condition of award that had been due on 10 November 2026, and began a review
aimed at lowering barriers for small and non-traditional businesses. The Small Business Administration's statement
([sba.gov](https://legacy.sba.gov/article/2026/07/13/sba-commends-us-department-wars-suspension-cmmc-phase-ii-small-defense-contractors))
cites cost, including an estimate of $593,800 per certification for small firms needing a third-party assessment, and more than
100,000 small businesses affected. The same reports say Phase 1 self-assessments and the DFARS obligations remain in effect.
That is the situation this project is built for: a small company that must assess itself, honestly and cheaply, with
evidence. Facts in this paragraph are as reported by the SBA; check current status before relying on them.

## The contracts decide the checklist

Which revision of 800-171 applies is set by the **contract**, not by the company. A business may hold contracts that
point at different revisions, so the profile lists every contract or subcontract that brings controlled information,
and the assessor works out which checklists to run.

| Agency group | Revision (owner's working assumption, 2026-10-06) | How to treat it |
|---|---|---|
| DoW | Rev 2 for now | Run the Rev 2 kit; re-check when the clause or class deviation changes |
| GSA | Rev 3 | Run the Rev 3 kit |
| Other civilian agency | 800-171, version not stated; assume Rev 3 | Run the Rev 3 kit and mark the result **assumed** |

These are statements the owner makes and dates, **not facts the tool decides**. Each contract records how the
owner knows (`contract_text`, `agency_notice` or `assumed`), where it is written (`revision_source`), and when it was
last checked (`last_verified`). The tool warns when a check is more than 90 days old, because the rules are moving
(for example a pending FAR clause on CUI). A contract that says nothing about the revision is shown as `assumed`
everywhere it appears.

**One evidence base, one view per contract.** If a company needs both Rev 2 and Rev 3, the assessor gathers evidence
once and reports each contract against its own revision ("contract X needs Rev 2: 3 objectives unmet").
NIST's Rev 2 to Rev 3 mapping lets one finding count toward both. The company's weakest results, not its average,
decide whether a contract is met.

## What the assessor does with the profile

1. **Chooses the kits** from the contracts (Rev 2, Rev 3, or both).
2. **Controls "not applicable".** An objective can be marked N/A only with a reason that points at a profile fact
   ("`owner_is_it_admin = yes`, so separation of duties cannot be implemented; compensating controls are ..."). The grader
   checks that the reason is there.
3. **Picks scan targets** from `[assessment] targets` and each system's `ssh_alias`. A system with no alias is
   documented but not scanned, and the report says so.
4. **Adjusts evidence expectations.** For a nano or micro business the owner's own attestation can stand in for an interview,
   and the tool says that is what was used. Objectives needing a person produce a short questionnaire.
5. **Suggests parameter values** only as examples, labelled "typical for a company this size". The organization
   decides parameters; the profile never does.
6. **Explains results** in plain language, with the stated size and roles at the top of every report.

## Size bands (decided)

The profile uses the categories in the article above, for consistency with the published data. The band is **worked out from
the number of employees** that the owner enters, not typed in separately, so the two cannot disagree. Under 20 employees is
in scope; a larger number gets a warning. Two differences from everyday usage are intentional: "nano" here means fewer than 5
employees (not "under 15"), and there is no separate band for a company of one: it is nano, and the role questions
(`owner_is_it_admin`, `security_lead`) capture what makes a one-person company different.

## The capability statement

A capability statement (or a similar one-page company description) is something almost every contractor already has.
A trial on a real one showed what a program can read from it reliably: industry codes (NAICS), registration identifiers,
the customer mix (defense, civilian, commercial, space), the facility type, the list of services, and **the security
claims the company makes about itself**. It does not say how many people work there, which systems exist or which
contracts carry which revision, so those stay owner-supplied.

It is used three ways:

1. **Seeding.** `[business]` is proposed from the statement and the owner confirms or corrects every value. Nothing is
   accepted silently.
2. **A claims check.** A statement such as "configured to meet FAR requirements" is a public claim. The assessor lists
   each security claim it finds and compares it with the assessment result, so a company sees where its own marketing is
   ahead of its evidence.
3. **The prime-contractor summary.** A short summary a prime can ask a subcontractor for: business identity, the
   contracts and revisions that apply, the overall result per contract, and the claims check, drawn from the profile and
   the latest assessment. The company decides what to send.

The statement's identifiers (registration numbers, phone, email) stay on the machine and are never sent to the AI.

## Outside parties

An outside party is listed **only when it has hands on the systems**, remote (tunnelling in) or on site, with the
systems it covers and where its obligations are written. A cloud or software service that merely hosts data is not an
outside party in this sense; it is described as a system, with the provider's authorization level if a contract asks
for one.

## Size is private, and the profile is honest

Most small businesses do not publish headcount, and many prefer to look larger than they are. So the capability
statement is never used to estimate size: **the owner states the number of users directly, and it stays private.**
The AI is told only the band (nano, micro or mini), never the number. The assessment needs the true size because the
right answer to some objectives depends on it (for example separation of duties).

Two rules follow:

- **The tool never writes something it knows to be false.** The prime-contractor summary is built from what the
  company elects to include. It may leave out the size band, but it may not state a different one.
- **The claims check covers security claims only.** Marketing about capacity or reach ("supports programs across ...")
  is not examined. A claim such as "configured to meet FAR requirements" is compared with the assessment result, and the
  comparison is shown to the owner first, privately, never to anyone else.

## What the AI sees, and what it does not

The profile holds sensitive business facts (contract names, clauses, who holds which role). The assessor builds a
short **assessment context** from it for the AI: size band, role model, system kinds and whether each is outsourced,
and which revisions to assess. It **never** passes contract names, numbers, clauses, prime or subcontractor names,
or the company name. The profile file itself sits where the sandbox blocks the AI from reading it, like the answer keys.

## File format

Plain **INI**: sections in square brackets (`[organization]`), `key = value` lines, `#` notes and `;` notes at the end
of a line. Repeating things (contracts, systems) are numbered or named sections (`[contract.1]`, `[system.server1]`).

Why INI: it is readable and editable in any text editor, allows comments (a form people can understand), and is parsed
by Python's standard library on every supported version. Considered and rejected: JSON (no comments, unfriendly to
edit), YAML (needs an extra package), TOML (needs Python 3.11 or later; this tool runs on the Mac's built-in Python),
a sheet inside the measurement register (changes NIST's template).

A friendly checker will validate the file and explain problems in plain words ("`required_revision` must be 2, 3 or
unspecified"). Anything blank means unknown, and unknown stays unknown in the report.

## Privacy

`profile.ini` is private: it is in `.gitignore`, the sandbox blocks the AI from reading it, and only the example ships
in the repository.

## Out of scope for now

Sampling across many systems, role-based interviews, per-department owners and trend reporting. Also not planned:
voluntary sharing of anonymous counts (size band, agency group, prime or subcontract) among adopters; this is a reference
system, so there is no production user base to count. They matter for
larger organizations and are left for a later version if the community asks.

## Open questions

1. Which capability-statement formats should the seeding step read first? Word, Markdown and plain text need no extra software; PDF would need a reader.
2. Should the prime-contractor summary be a one-page document, a form, or both?
3. What counts as "hands on" for an outside party? Remote tunnel and on-site are in; is a screen-sharing help desk session in?
4. **Typical parameter values for each band** (still open and hard): where do they come from and who reviews them? Candidate approach: start from NIST's own guidance and public frameworks, publish them as clearly labelled examples with the reason for each, and let the community review them. They are never a requirement.

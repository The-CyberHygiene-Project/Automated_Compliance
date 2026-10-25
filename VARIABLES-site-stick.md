# Variable names for site-specific fill-in

One list of names so that the assessor, the policy and procedure templates, and the Site Stick that prepares them
all read the same facts. **The profile file is the single source**: every variable is a `section.key` from
`profile.ini` (see `profile.example.ini`). A template never invents a new name; it asks for one to be added here.

## Placeholder form

`{{section.key}}` in a template, for example `{{organization.name}}` or `{{decision.audit_retention_days}}`.

- A placeholder with no value is **left as written and listed in a fill-in report**, never guessed or blanked.
- A list value (several systems, several people) is written `{{systems.in_boundary | list}}`.
- A block that applies only when a fact is true is wrapped `{{#if facts.has_mail_service}} ... {{/if}}`, and
  the fact comes from the profile (this is the same rule as the assessor's "not applicable must cite a fact").
- Nothing in a template names a real organization, host, address or person.

## Names that already exist in `profile.ini`

`organization.name`, `organization.employees` (private), `organization.people` (private),
`organization.owner_is_it_admin`, `organization.security_lead`, `organization.independent_reviewer`,
`organization.other_personnel`, `organization.outside_it_provider`;
`roles.system_owner`, `roles.administrator`, `roles.security_officer`, `roles.approver_of_changes`;
`business.naics`, `business.customer_groups`, `business.facility_type`;
`scope.cui_types`, `scope.cui_stored_in`, `scope.boundary_note`;
`contract.N.label|agency_group|vehicle|information|clauses|required_revision|revision_basis|last_verified`;
`provider.NAME.name|access|covers|agreement`;
`system.NAME.kind|in_boundary|operating_system|administered_by|provider`.

## Names to add (the Site Stick fills these)

**Identity and organization**

| Name | Meaning |
|---|---|
| `organization.legal_name`, `organization.dba` | legal entity and trading name |
| `organization.location` | city and state (public form only) |
| `organization.owner_name`, `organization.owner_email` | owner / security lead |
| `organization.cage`, `organization.uei` | registration identifiers (private; never in published documents) |
| `site.domain`, `site.directory_base` | primary domain; directory base name derived from it |
| `site.admin_account`, `site.admin_email` | the administrator account |

**Network and hosts** (private; documentation-range addresses in any published template)

| Name | Meaning |
|---|---|
| `site.lan_subnet`, `site.lan_gateway` | protected network |
| `site.host.NAME.address`, `site.host.NAME.role` | one entry per device: host, services VM, storage, and so on |
| `site.wan.NAME.address` | public addresses, by service (web, mail, VPN) |
| `site.hostname.NAME` | service names built from the domain |

**Decisions** (each has a suggested default; the customer confirms it, and the document records who did and when)

| Name | Meaning |
|---|---|
| `decision.audit_retention_days` | how long audit records are kept |
| `decision.log_review_frequency` | how often logs are reviewed |
| `decision.patch_cadence`, `decision.critical_patch_hours` | routine and emergency patch timing |
| `decision.lockout_threshold`, `decision.lockout_minutes` | failed-logon limit and duration |
| `decision.password_min_length`, `decision.password_history` | credential rules |
| `decision.inactivity_disable_days` | disable an account unused this long |
| `decision.screen_lock_minutes` | idle lock |
| `decision.backup_frequency`, `decision.restore_test_frequency` | backup and restore testing |
| `decision.alert_notify_minutes` | time from detection to an alert reaching a person |
| `decision.incident_internal_notify_hours`, `decision.incident_contain_hours`, `decision.incident_recover_hours` | internal notice, containment and recovery targets |
| `decision.incident_report_hours` | external reporting deadline |
| `decision.review_cycle_months` | policy and risk review interval |
| `decision.visitor_log_required` | physical visitor record: yes / no |

**Facts that switch sections on or off**

`facts.has_mail_service`, `facts.has_nas`, `facts.has_remote_access`, `facts.has_wireless`,
`facts.has_mobile_devices`, `facts.has_outside_it_provider`, `facts.uses_local_ai`, `facts.uses_external_ai`,
`facts.has_removable_media`, `facts.has_public_services`.

## Who may see a value

Each name is tagged **public** (may appear in a published document), **private** (stays on the customer's machine),
or **never-to-AI** (the assessor receives only a band or yes/no, as `profile.example.ini` already does for headcount).
The Site Stick keeps that tag with the value so a publish step can refuse private ones.

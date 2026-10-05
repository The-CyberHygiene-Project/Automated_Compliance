# NIST SP 800-171A potential assessment methods and objects

Source: NIST SP 800-171A (June 2018), assessment procedures spreadsheet; copied mechanically, unchanged.

## Access Control


### 3.1.1 Limit system access to authorized users, processes acting on behalf of authorized users, and devices (including other systems).

- Examine: [SELECT FROM: Access control policy; procedures addressing account management; security plan; system design documentation; system configuration settings and associated documentation; list of active system accounts and the name of the individual associated with each account; list of conditions for group and role membership; notifications or records of recently transferred, separated, or terminated employees; list of recently disabled system accounts along with the name of the individual associated with each account; access authorization records; account management compliance reviews; system monitoring records; system audit logs and records; other relevant documents or records; list of devices and other systems authorized to connect to organizational systems].
- Interview: [SELECT FROM: Personnel with account management responsibilities; system or network administrators; personnel with information security responsibilities].
- Test: [SELECT FROM: Organizational processes for managing system accounts; mechanisms for implementing account management].


### 3.1.2 Limit system access to the types of transactions and functions that authorized users are permitted to execute.

- Examine: [SELECT FROM: Access control policy; procedures addressing access enforcement; security plan; system design documentation; list of approved authorizations (user privileges) including remote access authorizations; system configuration settings and associated documentation; system audit logs and records; other relevant documents or records].
- Interview: [SELECT FROM: Personnel with access enforcement responsibilities; system or network administrators; personnel with information security responsibilities; system developers].
- Test: [SELECT FROM: Mechanisms implementing access control policy].


### 3.1.3 Control the flow of CUI in accordance with approved authorizations.

- Examine: [SELECT FROM: Access control policy; information flow control policies; procedures addressing information flow enforcement; security plan; system design documentation; system configuration settings and associated documentation; list of information flow authorizations; system baseline configuration; system audit logs and records; other relevant documents or records].
- Interview: [SELECT FROM: System or network administrators; personnel with information security responsibilities; system developers].
- Test: [SELECT FROM: Mechanisms implementing information flow enforcement policy].


### 3.1.4 Separate the duties of individuals to reduce the risk of malevolent activity without collusion.

- Examine: [SELECT FROM: Access control policy; procedures addressing divisions of responsibility and separation of duties; security plan; system configuration settings and associated documentation; list of divisions of responsibility and separation of duties; system access authorizations; system audit logs and records; other relevant documents or records].
- Interview: [SELECT FROM: Personnel with responsibilities for defining divisions of responsibility and separation of duties; personnel with information security responsibilities; system or network administrators].
- Test: [SELECT FROM: Mechanisms implementing separation of duties policy].


### 3.1.5 Employ the principle of least privilege, including for specific security functions and privileged accounts.

- Examine: [SELECT FROM: Access control policy; procedures addressing account management; security plan; system design documentation; system configuration settings and associated documentation; list of active system accounts and the name of the individual associated with each account; list of conditions for group and role membership; notifications or records of recently transferred, separated, or terminated employees; list of recently disabled system accounts along with the name of the individual associated with each account; access authorization records; account management compliance reviews; system monitoring/audit records; other relevant documents or records; procedures addressing least privilege; list of security functions (deployed in hardware, software, and firmware) and security-relevant information for which access must be explicitly authorized; list of system-generated privileged accounts; list of system administration personnel].
- Interview: [SELECT FROM: Personnel with account management responsibilities; system or network administrators; personnel with information security responsibilities; personnel with responsibilities for defining least privileges necessary to accomplish specified tasks].
- Test: [SELECT FROM: Organizational processes for managing system accounts; mechanisms for implementing account management; mechanisms implementing least privilege functions; mechanisms prohibiting privileged access to the system].


### 3.1.6 Use non-privileged accounts or roles when accessing nonsecurity functions.

- Examine: [SELECT FROM: Access control policy; procedures addressing least privilege; security plan; list of system-generated security functions assigned to system accounts or roles; system configuration settings and associated documentation; system audit logs and records; other relevant documents or records].
- Interview: [SELECT FROM: Personnel with responsibilities for defining least privileges necessary to accomplish specified organizational tasks; personnel with information security responsibilities; system or network administrators].
- Test: [SELECT FROM: Mechanisms implementing least privilege functions].


### 3.1.7 Prevent non-privileged users from executing privileged functions and capture the execution of such functions in audit logs.

- Examine: [SELECT FROM: Access control policy; procedures addressing least privilege; security plan; system design documentation; list of privileged functions and associated user account assignments; system configuration settings and associated documentation; system audit logs and records; other relevant documents or records].
- Interview: [SELECT FROM: Personnel with responsibilities for defining least privileges necessary to accomplish specified tasks; personnel with information security responsibilities; system developers].
- Test: [SELECT FROM: Mechanisms implementing least privilege functions for non-privileged users; mechanisms auditing the execution of privileged functions].


### 3.1.8 Limit unsuccessful logon attempts.

- Examine: [SELECT FROM: Access control policy; procedures addressing unsuccessful logon attempts; security plan; system design documentation; system configuration settings and associated documentation; system audit logs and records; other relevant documents or records].
- Interview: [SELECT FROM: Personnel with information security responsibilities; system developers; system or network administrators].
- Test: [SELECT FROM: Mechanisms implementing access control policy for unsuccessful logon attempts].


### 3.1.9 Provide privacy and security notices consistent with applicable CUI rules.

- Examine: SELECT FROM: Access control policy; privacy and security policies, procedures addressing system use notification; documented approval of system use notification messages or banners; system audit logs and records; system design documentation; user acknowledgements of notification message or banner; security plan; system use notification messages; system configuration settings and associated documentation; other relevant documents or records].
- Interview: [SELECT FROM: System or network administrators; personnel with information security responsibilities; personnel with responsibility for providing legal advice; system developers].
- Test: [SELECT FROM: Mechanisms implementing system use notification].


### 3.1.10 Use session lock with pattern-hiding displays to prevent access and viewing of data after a period of inactivity.

- Examine: [SELECT FROM: Access control policy; procedures addressing session lock; procedures addressing identification and authentication; system design documentation; system configuration settings and associated documentation; security plan; other relevant documents or records].
- Interview: [SELECT FROM: System or network administrators; personnel with information security responsibilities; system developers].
- Test: [SELECT FROM: Mechanisms implementing access control policy for session lock].


### 3.1.11 Terminate (automatically) a user session after a defined condition.

- Examine: [SELECT FROM: Access control policy; procedures addressing session termination; system design documentation; security plan; system configuration settings and associated documentation; list of conditions or trigger events requiring session disconnect; system audit logs and records; other relevant documents or records].
- Interview: [SELECT FROM: System or network administrators; personnel with information security responsibilities; system developers].
- Test: [SELECT FROM: Mechanisms implementing user session termination].


### 3.1.12 Monitor and control remote access sessions.

- Examine: [SELECT FROM: Access control policy; procedures addressing remote access implementation and usage (including restrictions); configuration management plan; security plan; system configuration settings and associated documentation; remote access authorizations; system audit logs and records; other relevant documents or records].
- Interview: [SELECT FROM: Personnel with responsibilities for managing remote access connections; system or network administrators; personnel with information security responsibilities].
- Test: [SELECT FROM: Remote access management capability for the system].


### 3.1.13 Employ cryptographic mechanisms to protect the confidentiality of remote access sessions.

- Examine: [SELECT FROM: Access control policy; procedures addressing remote access to the system; security plan; system design documentation; system configuration settings and associated documentation; cryptographic mechanisms and associated configuration documentation; system audit logs and records; other relevant documents or records].
- Interview: [SELECT FROM: System or network administrators; personnel with information security responsibilities; system developers].
- Test: [SELECT FROM: Cryptographic mechanisms protecting remote access sessions].


### 3.1.14 Route remote access via managed access control points.

- Examine: [SELECT FROM: Access control policy; procedures addressing remote access to the system; security plan; system design documentation; list of all managed network access control points; system configuration settings and associated documentation; system audit logs and records; other relevant documents or records].
- Interview: [SELECT FROM: System or network administrators; personnel with information security responsibilities].
- Test: [SELECT FROM: Mechanisms routing all remote accesses through managed network access control points].


### 3.1.15 Authorize remote execution of privileged commands and remote access to security-relevant information.

- Examine: [SELECT FROM: Access control policy; procedures addressing remote access to the system; system configuration settings and associated documentation; security plan; system audit logs and records; other relevant documents or records].
- Interview: [SELECT FROM: System or network administrators; personnel with information security responsibilities].
- Test: [SELECT FROM: Mechanisms implementing remote access management].


### 3.1.16 Authorize wireless access prior to allowing such connections.

- Examine: [SELECT FROM: Access control policy; configuration management plan; procedures addressing wireless access implementation and usage (including restrictions); security plan; system design documentation; system configuration settings and associated documentation; wireless access authorizations; system audit logs and records; other relevant documents or records].
- Interview: [SELECT FROM: Personnel with responsibilities for managing wireless access connections; personnel with information security responsibilities].
- Test: [SELECT FROM: Wireless access management capability for the system].


### 3.1.17 Protect wireless access using authentication and encryption.

- Examine: [SELECT FROM: Access control policy; system design documentation; procedures addressing wireless implementation and usage (including restrictions); security plan; system configuration settings and associated documentation; system audit logs and records; other relevant documents or records].
- Interview: [SELECT FROM: System or network administrators; personnel with information security responsibilities; system developers].
- Test: [SELECT FROM: Mechanisms implementing wireless access protections to the system].


### 3.1.18 Control connection of mobile devices.

- Examine: [SELECT FROM: Access control policy; authorizations for mobile device connections to organizational systems; procedures addressing access control for mobile device usage (including restrictions); system design documentation; configuration management plan; security plan; system audit logs and records; system configuration settings and associated documentation; other relevant documents or records].
- Interview: [SELECT FROM: Personnel using mobile devices to access organizational systems; system or network administrators; personnel with information security responsibilities].
- Test: [SELECT FROM: Access control capability authorizing mobile device connections to organizational systems].


### 3.1.19 Encrypt CUI on mobile devices and mobile computing platforms.

- Examine: 
- Interview: 
- Test: 


### 3.1.20 Verify and control/limit connections to and use of external systems.

- Examine: [SELECT FROM: Access control policy; procedures addressing the use of external systems; terms and conditions for external systems; security plan; list of types of applications accessible from external systems; system configuration settings and associated documentation; other relevant documents or records].
- Interview: [SELECT FROM: Personnel with responsibilities for defining terms and conditions for use of external systems to access organizational systems; system or network administrators; personnel with information security responsibilities].
- Test: [SELECT FROM: Mechanisms implementing terms and conditions on use of external systems].


### 3.1.21 Limit use of organizational portable storage devices on external systems.

- Examine: [SELECT FROM: Access control policy; procedures addressing the use of external systems; security plan; system configuration settings and associated documentation; system connection or processing agreements; account management documents; other relevant documents or records].
- Interview: [SELECT FROM: Personnel with responsibilities for restricting or prohibiting use of organization-controlled storage devices on external systems; system or network administrators; personnel with information security responsibilities].
- Test: [SELECT FROM: Mechanisms implementing restrictions on use of portable storage devices].


### 3.1.22 Control CUI posted or processed on publicly accessible systems.

- Examine: [SELECT FROM: Access control policy; procedures addressing publicly accessible content; security plan; list of users authorized to post publicly accessible content on organizational systems; training materials and/or records; records of publicly accessible information reviews; records of response to nonpublic information on public websites; system audit logs and records; security awareness training records; other relevant documents or records].
- Interview: [SELECT FROM: Personnel with responsibilities for managing publicly accessible information posted on organizational systems; personnel with information security responsibilities].
- Test: [SELECT FROM: Mechanisms implementing management of publicly accessible content].


## Awareness and Training


### 3.2.1 Ensure that managers, systems administrators, and users of organizational systems are made aware of the security risks associated with their activities and of the applicable policies, standards, and procedures related to the security of those systems.

- Examine: [SELECT FROM: Security awareness and training policy; procedures addressing security awareness training implementation; relevant codes of federal regulations; security awareness training curriculum; security awareness training materials; security plan; training records; other relevant documents or records].
- Interview: [SELECT FROM: Personnel with responsibilities for security awareness training; personnel with information security responsibilities; personnel composing the general system user community].
- Test: [SELECT FROM: Mechanisms managing security awareness training; mechanisms managing role-based security training].


### 3.2.2 Ensure that organizational personnel are adequately trained to carry out their assigned information security-related duties and responsibilities.

- Examine: [SELECT FROM: Security awareness and training policy; procedures addressing security training implementation; codes of federal regulations; security training curriculum; security training materials; security plan; training records; other relevant documents or records].
- Interview: [SELECT FROM: Personnel with responsibilities for role-based security training; personnel with assigned system security roles and responsibilities].
- Test: [SELECT FROM: Mechanisms managing role-based security training].


### 3.2.3 Provide security awareness training on recognizing and reporting potential indicators of insider threat.

- Examine: [SELECT FROM: Security awareness and training policy; procedures addressing security awareness training implementation; security awareness training curriculum; security awareness training materials; insider threat policy and procedures; security plan; other relevant documents or records].
- Interview: [SELECT FROM: Personnel that participate in security awareness training; personnel with responsibilities for basic security awareness training; personnel with information security responsibilities].
- Test: [SELECT FROM: Mechanisms managing insider threat training].


## Audit and Accountability


### 3.3.1 Create and retain system audit logs and records to the extent needed to enable the monitoring, analysis, investigation, and reporting of unlawful or unauthorized system activity.

- Examine: [SELECT FROM: Audit and accountability policy; procedures addressing auditable events; security plan; system design documentation; system configuration settings and associated documentation; system audit logs and records; system auditable events; system incident reports; other relevant documents or records].
- Interview: [SELECT FROM: Personnel with audit and accountability responsibilities; personnel with information security responsibilities; system or network administrators].
- Test: [SELECT FROM: Mechanisms implementing system audit logging].


### 3.3.2 Ensure that the actions of individual system users can be uniquely traced to those users so they can be held accountable for their actions.

- Examine: [SELECT FROM: Audit and accountability policy; procedures addressing audit records and event types; security plan; system design documentation; system configuration settings and associated documentation; system audit logs and records; system events; system incident reports; other relevant documents or records].
- Interview: [SELECT FROM: Personnel with audit and accountability responsibilities; personnel with information security responsibilities; system or network administrators].
- Test: [SELECT FROM: Mechanisms implementing system audit logging].


### 3.3.3 Review and update logged events.

- Examine: [SELECT FROM: Audit and accountability policy; procedures addressing audit records and event types; security plan; list of organization-defined event types to be logged; reviewed and updated records of logged event types; system audit logs and records; system incident reports; other relevant documents or records].
- Interview: [SELECT FROM: Personnel with audit and accountability responsibilities; personnel with information security responsibilities].
- Test: [SELECT FROM: Mechanisms supporting review and update of logged event types].


### 3.3.4 Alert in the event of an audit logging process failure.

- Examine: [SELECT FROM: Audit and accountability policy; procedures addressing response to audit logging processing failures; system design documentation; security plan; system configuration settings and associated documentation; list of personnel to be notified in case of an audit logging processing failure; system incident reports; system audit logs and records; other relevant documents or records].
- Interview: [SELECT FROM: Personnel with audit and accountability responsibilities; personnel with information security responsibilities; system or network administrators; system developers].
- Test: [SELECT FROM: Mechanisms implementing system response to audit logging processing failures].


### 3.3.5 Correlate audit record review, analysis, and reporting processes for investigation and response to indications of unlawful, unauthorized, suspicious, or unusual activity.

- Examine: [SELECT FROM: Audit and accountability policy; procedures addressing audit record review, analysis, and reporting; security plan; system design documentation; system configuration settings and associated documentation; system audit logs and records across different repositories; other relevant documents or records].
- Interview: [SELECT FROM: Personnel with audit record review, analysis, and reporting responsibilities; personnel with information security responsibilities].
- Test: : [SELECT FROM: Mechanisms supporting analysis and correlation of audit records].


### 3.3.6 Provide audit record reduction and report generation to support on-demand analysis and reporting.

- Examine: [SELECT FROM: Audit and accountability policy; procedures addressing audit record reduction and report generation; system design documentation; security plan; system configuration settings and associated documentation; audit record reduction, review, analysis, and reporting tools; system audit logs and records; other relevant documents or records].
- Interview: [SELECT FROM: Personnel with audit record reduction and report generation responsibilities; personnel with information security responsibilities].
- Test: [SELECT FROM: Audit record reduction and report generation capability].


### 3.3.7 Provide a system capability that compares and synchronizes internal system clocks with an authoritative source to generate time stamps for audit records.

- Examine: [SELECT FROM: Audit and accountability policy; procedures addressing time stamp generation; system design documentation; security plan; system configuration settings and associated documentation; system audit logs and records; other relevant documents or records].
- Interview: [SELECT FROM: Personnel with information security responsibilities; system or network administrators; system developers].
- Test: [SELECT FROM: Mechanisms implementing time stamp generation].


### 3.3.8 Protect audit information and audit logging tools from unauthorized access, modification, and deletion.

- Examine: [SELECT FROM: Audit and accountability policy; access control policy and procedures; procedures addressing protection of audit information; security plan; system design documentation; system configuration settings and associated documentation, system audit logs and records; audit logging tools; other relevant documents or records].
- Interview: [SELECT FROM: Personnel with audit and accountability responsibilities; personnel with information security responsibilities; system or network administrators; system developers].
- Test: [SELECT FROM: Mechanisms implementing audit information protection].


### 3.3.9 Limit management of audit logging functionality to a subset of privileged users.

- Examine: [SELECT FROM: Audit and accountability policy; access control policy and procedures; procedures addressing protection of audit information; security plan; system design documentation; system configuration settings and associated documentation; access authorizations; system-generated list of privileged users with access to management of audit logging functionality; access control list; system audit logs and records; other relevant documents or records].
- Interview: [SELECT FROM: Personnel with audit and accountability responsibilities; personnel with information security responsibilities; system or network administrators; system developers].
- Test: [SELECT FROM: Mechanisms managing access to audit logging functionality].


## Configuration Management


### 3.4.1 Establish and maintain baseline configurations and inventories of organizational systems (including hardware, software, firmware, and documentation) throughout the respective system development life cycles.

- Examine: [SELECT FROM: Configuration management policy; procedures addressing the baseline configuration of the system; procedures addressing system inventory; security plan; configuration management plan; system inventory records; inventory review and update records; enterprise architecture documentation; system design documentation; system architecture and configuration documentation; system configuration settings and associated documentation; change control records; system component installation records; system component removal records; other relevant documents or records].
- Interview: [SELECT FROM: Personnel with configuration management responsibilities; personnel with responsibilities for establishing the system inventory; personnel with responsibilities for updating the system inventory; personnel with information security responsibilities; system or network administrators].
- Test: [SELECT FROM: Organizational processes for managing baseline configurations; mechanisms supporting configuration control of the baseline configuration; organizational processes for developing and documenting an inventory of system components; organizational processes for updating inventory of system components; mechanisms supporting or implementing the system inventory; mechanisms implementing updating of the system inventory].


### 3.4.2 Establish and enforce security configuration settings for information technology products employed in organizational systems.

- Examine: [SELECT FROM: Configuration management policy; procedures addressing configuration settings for the system; configuration management plan; security plan; system design documentation; system configuration settings and associated documentation; security configuration checklists; evidence supporting approved deviations from established configuration settings; change control records; system audit logs and records; other relevant documents or records].
- Interview: [SELECT FROM: Personnel with security configuration management responsibilities; personnel with information security responsibilities; system or network administrators].
- Test: [SELECT FROM: Organizational processes for managing configuration settings; mechanisms that implement, monitor, and/or control system configuration settings; mechanisms that identify and/or document deviations from established configuration settings].


### 3.4.3 Track, review, approve or disapprove, and log changes to organizational systems.

- Examine: [SELECT FROM: Configuration management policy; procedures addressing system configuration change control; configuration management plan; system architecture and configuration documentation; security plan; change control records; system audit logs and records; change control audit and review reports; agenda/minutes from configuration change control oversight meetings; other relevant documents or records].
- Interview: [SELECT FROM: Personnel with configuration change control responsibilities; personnel with information security responsibilities; system or network administrators; members of change control board or similar].
- Test: [SELECT FROM: Organizational processes for configuration change control; mechanisms that implement configuration change control].


### 3.4.4 Analyze the security impact of changes prior to implementation.

- Examine: [SELECT FROM: Configuration management policy; procedures addressing security impact analysis for changes to the system; configuration management plan; security impact analysis documentation; security plan; analysis tools and associated outputs; change control records; system audit logs and records; other relevant documents or records].
- Interview: [SELECT FROM: Personnel with responsibility for conducting security impact analysis; personnel with information security responsibilities; system or network administrators].
- Test: [SELECT FROM: Organizational processes for security impact analysis].


### 3.4.5 Define, document, approve, and enforce physical and logical access restrictions associated with changes to organizational systems.

- Examine: [SELECT FROM: Configuration management policy; procedures addressing access restrictions for changes to the system; security plan; configuration management plan; system design documentation; system architecture and configuration documentation; system configuration settings and associated documentation; logical access approvals; physical access approvals; access credentials; change control records; system audit logs and records; other relevant documents or records].
- Interview: [SELECT FROM: Personnel with logical access control responsibilities; personnel with physical access control responsibilities; personnel with information security responsibilities; system or network administrators].
- Test: [SELECT FROM: Organizational processes for managing access restrictions associated with changes to the system; mechanisms supporting, implementing, and enforcing access restrictions associated with changes to the system].


### 3.4.6 Employ the principle of least functionality by configuring organizational systems to provide only essential capabilities.

- Examine: [SELECT FROM: Configuration management policy; configuration management plan; procedures addressing least functionality in the system; security plan; system design documentation; system configuration settings and associated documentation; security configuration checklists; other relevant documents or records].
- Interview: [SELECT FROM: Personnel with security configuration management responsibilities; personnel with information security responsibilities; system or network administrators].
- Test: [SELECT FROM: Organizational processes prohibiting or restricting functions, ports, protocols, or services; mechanisms implementing restrictions or prohibition of functions, ports, protocols, or services].


### 3.4.7 Restrict, disable, or prevent the use of nonessential programs, functions, ports, protocols, and services.

- Examine: [SELECT FROM: Configuration management policy; procedures addressing least functionality in the system; configuration management plan; security plan; system design documentation; system configuration settings and associated documentation; specifications for preventing software program execution; security configuration checklists; documented reviews of programs, functions, ports, protocols, and/or services; change control records; system audit logs and records; other relevant documents or records].
- Interview: [SELECT FROM: Personnel with responsibilities for reviewing programs, functions, ports, protocols, and services on the system; personnel with information security responsibilities; system or network administrators; system developers].
- Test: [SELECT FROM: Organizational processes for reviewing and disabling nonessential programs, functions, ports, protocols, or services; mechanisms implementing review and handling of nonessential programs, functions, ports, protocols, or services; organizational processes preventing program execution on the system; organizational processes for software program usage and restrictions; mechanisms supporting or implementing software program usage and restrictions; mechanisms preventing program execution on the system].


### 3.4.8 Apply deny-by-exception (blacklisting) policy to prevent the use of unauthorized software or deny-all, permit-by-exception (whitelisting) policy to allow the execution of authorized software.

- Examine: [SELECT FROM: Configuration management policy; procedures addressing least functionality in the system; security plan; configuration management plan; system design documentation; system configuration settings and associated documentation; list of software programs not authorized to execute on the system; list of software programs authorized to execute on the system; security configuration checklists; review and update records associated with list of authorized or unauthorized software programs; change control records; system audit logs and records; other relevant documents or records].
- Interview: [SELECT FROM: Personnel with responsibilities for identifying software authorized or not authorized to execute on the system; personnel with information security responsibilities; system or network administrators].
- Test: [SELECT FROM: Organizational process for identifying, reviewing, and updating programs authorized or not authorized to execute on the system; process for implementing blacklisting or whitelisting; mechanisms supporting or implementing blacklisting or whitelisting].


### 3.4.9 Control and monitor user-installed software.

- Examine: [SELECT FROM: Configuration management policy; procedures addressing user installed software; configuration management plan; security plan; system design documentation; system configuration settings and associated documentation; list of rules governing user-installed software; system monitoring records; system audit logs and records; continuous monitoring strategy; other relevant documents or records].
- Interview: [SELECT FROM: Personnel with responsibilities for governing user-installed software; personnel operating, using, or maintaining the system; personnel monitoring compliance with user-installed software policy; personnel with information security responsibilities; system or network administrators].
- Test: [SELECT FROM: Organizational processes governing user-installed software on the system; mechanisms enforcing rules or methods for governing the installation of software by users; mechanisms monitoring policy compliance].


## Identification and Authentication


### 3.5.1 Identify system users, processes acting on behalf of users, and devices.

- Examine: [SELECT FROM: Identification and authentication policy; procedures addressing user identification and authentication; security plan, system design documentation; system configuration settings and associated documentation; system audit logs and records; list of system accounts; other relevant documents or records].
- Interview: [SELECT FROM: Personnel with system operations responsibilities; personnel with information security responsibilities; system or network administrators; personnel with account management responsibilities; system developers].
- Test: [SELECT FROM: Organizational processes for uniquely identifying and authenticating users; mechanisms supporting or implementing identification and authentication capability].


### 3.5.2 Authenticate (or verify) the identities of users, processes, or devices, as a prerequisite to allowing access to organizational systems

- Examine: [SELECT FROM: Identification and authentication policy; procedures addressing authenticator management; security plan; system design documentation; system configuration settings and associated documentation; list of system authenticator types; change control records associated with managing system authenticators; system audit logs and records; other relevant documents or records].
- Interview: [SELECT FROM: Personnel with authenticator management responsibilities; personnel with information security responsibilities; system or network administrators].
- Test: [SELECT FROM: Mechanisms supporting or implementing authenticator management capability].


### 3.5.3 Use multifactor authentication for local and network access to privileged accounts and for network access to non-privileged accounts.

- Examine: [SELECT FROM: Identification and authentication policy; procedures addressing user identification and authentication; security plan; system design documentation; system configuration settings and associated documentation; system audit logs and records; list of system accounts; other relevant documents or records].
- Interview: [SELECT FROM: Personnel with system operations responsibilities; personnel with account management responsibilities; personnel with information security responsibilities; system or network administrators; system developers].
- Test: [SELECT FROM: Mechanisms supporting or implementing multifactor authentication capability].


### 3.5.4 Employ replay-resistant authentication mechanisms for network access to privileged and non-privileged accounts.

- Examine: [SELECT FROM: Identification and authentication policy; procedures addressing user identification and authentication; security plan; system design documentation; system configuration settings and associated documentation; system audit logs and records; list of privileged system accounts; other relevant documents or records].
- Interview: [SELECT FROM: Personnel with system operations responsibilities; personnel with account management responsibilities; personnel with information security responsibilities; system or network administrators; system developers].
- Test: [SELECT FROM: Mechanisms supporting or implementing identification and authentication capability or replay resistant authentication mechanisms].


### 3.5.5 Prevent reuse of identifiers for a defined period.

- Examine: [SELECT FROM: Identification and authentication policy; procedures addressing identifier management; procedures addressing account management; security plan; system design documentation; system configuration settings and associated documentation; list of system accounts; list of identifiers generated from physical access control devices; other relevant documents or records].
- Interview: [SELECT FROM: Personnel with identifier management responsibilities; personnel with information security responsibilities; system or network administrators; system developers].
- Test: [SELECT FROM: Mechanisms supporting or implementing identifier management].


### 3.5.6 Disable identifiers after a defined period of inactivity.

- Examine: [SELECT FROM: Identification and authentication policy; procedures addressing identifier management; procedures addressing account management; security plan; system design documentation; system configuration settings and associated documentation; list of system accounts; list of identifiers generated from physical access control devices; other relevant documents or records].
- Interview: [SELECT FROM: Personnel with identifier management responsibilities; personnel with information security responsibilities; system or network administrators; system developers].
- Test: [SELECT FROM: Mechanisms supporting or implementing identifier management].


### 3.5.7 Enforce a minimum password complexity and change of characters when new passwords are created.

- Examine: [SELECT FROM: Identification and authentication policy; password policy; procedures addressing authenticator management; security plan; system design documentation; system configuration settings and associated documentation; password configurations and associated documentation; other relevant documents or records].
- Interview: [SELECT FROM: Personnel with authenticator management responsibilities; personnel with information security responsibilities; system or network administrators; system developers].
- Test: [SELECT FROM: Mechanisms supporting or implementing password-based authenticator management capability].


### 3.5.8 Prohibit password reuse for a specified number of generations.

- Examine: [SELECT FROM: Identification and authentication policy; password policy; procedures addressing authenticator management; security plan; system design documentation; system configuration settings and associated documentation; password configurations and associated documentation; other relevant documents or records].
- Interview: [SELECT FROM: Personnel with authenticator management responsibilities; personnel with information security responsibilities; system or network administrators; system developers].
- Test: [SELECT FROM: Mechanisms supporting or implementing password-based authenticator management capability].


### 3.5.9 Allow temporary password use for system logons with an immediate change to a permanent password

- Examine: [SELECT FROM: Identification and authentication policy; password policy; procedures addressing authenticator management; security plan; system design documentation; system configuration settings and associated documentation; password configurations and associated documentation; other relevant documents or records].
- Interview: [SELECT FROM: Personnel with authenticator management responsibilities; personnel with information security responsibilities; system or network administrators; system developers].
- Test: [SELECT FROM: Mechanisms supporting or implementing password-based authenticator management capability].


### 3.5.10 Store and transmit only cryptographically-protected passwords.

- Examine: [SELECT FROM: Identification and authentication policy; password policy; procedures addressing authenticator management; security plan; system design documentation; system configuration settings and associated documentation; password configurations and associated documentation; other relevant documents or records].
- Interview: [SELECT FROM: Personnel with authenticator management responsibilities; personnel with information security responsibilities; system or network administrators; system developers].
- Test: [SELECT FROM: Mechanisms supporting or implementing password-based authenticator management capability].


### 3.5.11 Obscure feedback of authentication information.

- Examine: [SELECT FROM: Identification and authentication policy; procedures addressing authenticator feedback; security plan; system design documentation; system configuration settings and associated documentation; system audit logs and records; other relevant documents or records].
- Interview: [SELECT FROM: Personnel with information security responsibilities; system or network administrators; system developers].
- Test: [SELECT FROM: Mechanisms supporting or implementing the obscuring of feedback of authentication information during authentication].


## Incident Response


### 3.6.1 Establish an operational incident-handling capability for organizational systems that includes preparation, detection, analysis, containment, recovery, and user response activities.

- Examine: [SELECT FROM: Incident response policy; contingency planning policy; procedures addressing incident handling; procedures addressing incident response assistance; incident response plan; contingency plan; security plan; procedures addressing incident response training; incident response training curriculum; incident response training materials; incident response training records; other relevant documents or records].
- Interview: [SELECT FROM: Personnel with incident handling responsibilities; personnel with contingency planning responsibilities; personnel with incident response training and operational responsibilities; personnel with incident response assistance and support responsibilities; personnel with access to incident response support and assistance capability; personnel with information security responsibilities].
- Test: [SELECT FROM: Incident-handling capability for the organization; organizational processes for incident response assistance; mechanisms supporting or implementing incident response assistance].


### 3.6.2 Track, document, and report incidents to designated officials and/or authorities both internal and external to the organization.

- Examine: [SELECT FROM: Incident response policy; procedures addressing incident monitoring; incident response records and documentation; procedures addressing incident reporting; incident reporting records and documentation; incident response plan; security plan; other relevant documents or records].
- Interview: [SELECT FROM: Personnel with incident monitoring responsibilities; personnel with incident reporting responsibilities; personnel who have or should have reported incidents; personnel (authorities) to whom incident information is to be reported; personnel with information security responsibilities].
- Test: [SELECT FROM: Incident monitoring capability for the organization; mechanisms supporting or implementing tracking and documenting of system security incidents; organizational processes for incident reporting; mechanisms supporting or implementing incident reporting].


### 3.6.3 Test the organizational incident response capability.

- Examine: [SELECT FROM: Incident response policy; contingency planning policy; procedures addressing incident response testing; procedures addressing contingency plan testing; incident response testing material; incident response test results; incident response test plan; incident response plan; contingency plan; security plan; other relevant documents or records].
- Interview: [SELECT FROM: Personnel with incident response testing responsibilities; personnel with information security responsibilities].
- Test: 


## Maintenance


### 3.7.1 Perform maintenance on organizational systems.

- Examine: [SELECT FROM: System maintenance policy; procedures addressing controlled system maintenance; maintenance records; manufacturer or vendor maintenance specifications; equipment sanitization records; media sanitization records; security plan; other relevant documents or records].
- Interview: [select from: Personnel with system maintenance responsibilities; personnel with information security responsibilities; personnel responsible for media sanitization; system or network administrators].
- Test: [SELECT FROM: Organizational processes for scheduling, performing, documenting, reviewing, approving, and monitoring maintenance and repairs for systems; organizational processes for sanitizing system components; mechanisms supporting or implementing controlled maintenance; mechanisms implementing sanitization of system components].


### 3.7.2 Provide controls on the tools, techniques, mechanisms, and personnel used to conduct system maintenance.

- Examine: [SELECT FROM: System maintenance policy; procedures addressing system maintenance tools and media; maintenance records; system maintenance tools and associated documentation; maintenance tool inspection records; security plan; other relevant documents or records].
- Interview: [SELECT FROM: Personnel with system maintenance responsibilities; personnel with information security responsibilities].
- Test: [SELECT FROM: Organizational processes for approving, controlling, and monitoring maintenance tools; mechanisms supporting or implementing approval, control, and monitoring of maintenance tools; organizational processes for inspecting maintenance tools; mechanisms supporting or implementing inspection of maintenance tools; organizational process for inspecting media for malicious code; mechanisms supporting or implementing inspection of media used for maintenance].


### 3.7.3 Ensure equipment removed for off-site maintenance is sanitized of any CUI.

- Examine: [SELECT FROM: System maintenance policy; procedures addressing controlled system maintenance; maintenance records; manufacturer or vendor maintenance specifications; equipment sanitization records; media sanitization records; security plan; other relevant documents or records].
- Interview: [SELECT FROM: Personnel with system maintenance responsibilities; personnel with information security responsibilities; personnel responsible for media sanitization; system or network administrators].
- Test: [select from: Organizational processes for scheduling, performing, documenting, reviewing, approving, and monitoring maintenance and repairs for systems; organizational processes for sanitizing system components; mechanisms supporting or implementing controlled maintenance; mechanisms implementing sanitization of system components].


### 3.7.4 Check media containing diagnostic and test programs for malicious code before the media are used in organizational systems

- Examine: [SELECT FROM: System maintenance policy; procedures addressing system maintenance tools; system maintenance tools and associated documentation; maintenance records; security plan; other relevant documents or records].
- Interview: [SELECT FROM: Personnel with system maintenance responsibilities; personnel with information security responsibilities].
- Test: [select from: Organizational process for inspecting media for malicious code; mechanisms supporting or implementing inspection of media used for maintenance].


### 3.7.5 Require multifactor authentication to establish nonlocal maintenance sessions via external network connections and terminate such connections when nonlocal maintenance is complete.

- Examine: [SELECT FROM: System maintenance policy; procedures addressing nonlocal system maintenance; security plan; system design documentation; system configuration settings and associated documentation; maintenance records; diagnostic records; other relevant documents or records].
- Interview: [SELECT FROM: Personnel with system maintenance responsibilities; personnel with information security responsibilities; system or network administrators].
- Test: [select from: Organizational processes for managing nonlocal maintenance; mechanisms implementing, supporting, and managing nonlocal maintenance; mechanisms for strong authentication of nonlocal maintenance diagnostic sessions; mechanisms for terminating nonlocal maintenance sessions and network connections].


### 3.7.6 Supervise the maintenance activities of maintenance personnel without required access authorization.

- Examine: [SELECT FROM: System maintenance policy; procedures addressing maintenance personnel; service provider contracts; service-level agreements; list of authorized personnel; maintenance records; access control records; security plan; other relevant documents or records].
- Interview: [SELECT FROM: Personnel with system maintenance responsibilities; personnel with information security responsibilities].
- Test: [SELECT FROM: Organizational processes for authorizing and managing maintenance personnel; mechanisms supporting or implementing authorization of maintenance personnel].


## Media Protection


### 3.8.1 Protect (i.e., physically control and securely store) system media containing CUI, both paper and digital.

- Examine: [SELECT FROM: System media protection policy; procedures addressing media access restrictions; access control policy and procedures; physical and environmental protection policy and procedures; security plan; media storage facilities; access control records; other relevant documents or records].
- Interview: [SELECT FROM: Personnel with system media protection responsibilities; personnel with information security responsibilities; system or network administrators].
- Test: [SELECT FROM: Organizational processes for restricting information media; mechanisms supporting or implementing media access restrictions].


### 3.8.2 Limit access to CUI on system media to authorized users.

- Examine: [SELECT FROM: System media protection policy; procedures addressing media storage; physical and environmental protection policy and procedures; access control policy and procedures; security plan; system media; designated controlled areas; other relevant documents or records].
- Interview: [SELECT FROM: Personnel with system media protection and storage responsibilities; personnel with information security responsibilities].
- Test: [SELECT FROM: Organizational processes for storing media; mechanisms supporting or implementing secure media storage and media protection].


### 3.8.3 Sanitize or destroy system media containing CUI before disposal or release for reuse.

- Examine: [SELECT FROM: System media protection policy; procedures addressing media sanitization and disposal; applicable standards and policies addressing media sanitization; security plan; media sanitization records; system audit logs and records; system design documentation; system configuration settings and associated documentation; other relevant documents or records].
- Interview: [SELECT FROM: Personnel with media sanitization responsibilities; personnel with information security responsibilities; system or network administrators].
- Test: [SELECT FROM: Organizational processes for media sanitization; mechanisms supporting or implementing media sanitization].


### 3.8.4 Mark media with necessary CUI markings and distribution limitations.

- Examine: [SELECT FROM: System media protection policy; procedures addressing media marking; physical and environmental protection policy and procedures; security plan; list of system media marking security attributes; designated controlled areas; other relevant documents or records].
- Interview: [SELECT FROM: Personnel with system media protection and marking responsibilities; personnel with information security responsibilities].
- Test: [SELECT FROM: Organizational processes for marking information media; mechanisms supporting or implementing media marking].


### 3.8.5 Control access to media containing CUI and maintain accountability for media during transport outside of controlled areas.

- Examine: SELECT FROM: System media protection policy; procedures addressing media storage; physical and environmental protection policy and procedures; access control policy and procedures; security plan; system media; designated controlled areas; other relevant documents or records].
- Interview: [SELECT FROM: Personnel with system media protection and storage responsibilities; personnel with information security responsibilities; system or network administrators].
- Test: [SELECT FROM: Organizational processes for storing media; mechanisms supporting or implementing media storage and media protection].


### 3.8.6 Implement cryptographic mechanisms to protect the confidentiality of CUI stored on digital media during transport unless otherwise protected by alternative physical safeguards.

- Examine: [SELECT FROM: System media protection policy; procedures addressing media transport; system design documentation; security plan; system configuration settings and associated documentation; system media transport records; system audit logs and records; other relevant documents or records].
- Interview: [SELECT FROM: Personnel with system media transport responsibilities; personnel with information security responsibilities].
- Test: [SELECT FROM: Cryptographic mechanisms protecting information on digital media during transportation outside controlled areas].


### 3.8.7 Control the use of removable media on system components.

- Examine: [SELECT FROM: System media protection policy; system use policy; procedures addressing media usage restrictions; security plan; rules of behavior; system design documentation; system configuration settings and associated documentation; system audit logs and records; other relevant documents or records].
- Interview: [SELECT FROM: Personnel with system media use responsibilities; personnel with information security responsibilities; system or network administrators].
- Test: [SELECT FROM: Organizational processes for media use; mechanisms restricting or prohibiting use of system media on systems or system components].


### 3.8.8 Prohibit the use of portable storage devices when such devices have no identifiable owner.

- Examine: [SELECT FROM: System media protection policy; system use policy; procedures addressing media usage restrictions; security plan; rules of behavior; system design documentation; system configuration settings and associated documentation; system audit logs and records; other relevant documents or records].
- Interview: [SELECT FROM: Personnel with system media use responsibilities; personnel with information security responsibilities; system or network administrators].
- Test: [SELECT FROM: Organizational processes for media use; mechanisms prohibiting use of media on systems or system components].


### 3.8.9 Protect the confidentiality of backup CUI at storage locations.

- Examine: [SELECT FROM: Procedures addressing system backup; security plan; backup storage location(s); system backup logs or records; other relevant documents or records].
- Interview: [[SELECT FROM: Personnel with system backup responsibilities; personnel with information security responsibilities].
- Test: [SELECT FROM: Organizational processes for conducting system backups; mechanisms supporting or implementing system backups].


## Personnel Security


### 3.9.1 Screen individuals prior to authorizing access to organizational systems containing CUI.

- Examine: [SELECT FROM: Personnel security policy; procedures addressing personnel screening; records of screened personnel; security plan; other relevant documents or records].
- Interview: [SELECT FROM: Personnel with personnel security responsibilities; personnel with information security responsibilities].
- Test: [SELECT FROM: Organizational processes for personnel screening].


### 3.9.2 Ensure that organizational systems containing CUI are protected during and after personnel actions such as terminations and transfers.

- Examine: [SELECT FROM: Personnel security policy; procedures addressing personnel transfer and termination; records of personnel transfer and termination actions; list of system accounts; records of terminated or revoked authenticators and credentials; records of exit interviews; other relevant documents or records].
- Interview: [SELECT FROM: Personnel with personnel security responsibilities; personnel with account management responsibilities; system or network administrators; personnel with information security responsibilities].
- Test: [SELECT FROM: Organizational processes for personnel transfer and termination; mechanisms supporting or implementing personnel transfer and termination notifications; mechanisms for disabling system access and revoking authenticators].


### 3.10.1 Limit physical access to organizational systems, equipment, and the respective operating environments to authorized individuals.

- Examine: [SELECT FROM: Physical and environmental protection policy; procedures addressing physical access authorizations; security plan; authorized personnel access list; authorization credentials; physical access list reviews; physical access termination records and associated documentation; other relevant documents or records].
- Interview: [SELECT FROM: Personnel with physical access authorization responsibilities; personnel with physical access to system facility; personnel with information security responsibilities].
- Test: [SELECT FROM: Organizational processes for physical access authorizations; mechanisms supporting or implementing physical access authorizations].


## Physical Protection


### 3.10.2 Protect and monitor the physical facility and support infrastructure for organizational systems.

- Examine: [SELECT FROM: Physical and environmental protection policy; procedures addressing physical access monitoring; security plan; physical access logs or records; physical access monitoring records; physical access log reviews; other relevant documents or records].
- Interview: [SELECT FROM: Personnel with physical access monitoring responsibilities; personnel with incident response responsibilities; personnel with information security responsibilities].
- Test: [SELECT FROM: Organizational processes for monitoring physical access; mechanisms supporting or implementing physical access monitoring; mechanisms supporting or implementing the review of physical access logs].


### 3.10.3 Escort visitors and monitor visitor activity.

- Examine: [SELECT FROM: Physical and environmental protection policy; procedures addressing physical access control; security plan; physical access control logs or records; inventory records of physical access control devices; system entry and exit points; records of key and lock combination changes; storage locations for physical access control devices; physical access control devices; list of security safeguards controlling access to designated publicly accessible areas within facility; other relevant documents or records].
- Interview: [SELECT FROM: Personnel with physical access control responsibilities; personnel with information security responsibilities].
- Test: [SELECT FROM: Organizational processes for physical access control; mechanisms supporting or implementing physical access control; physical access control devices].


### 3.10.4 Maintain audit logs of physical access.

- Examine: [SELECT FROM: Physical and environmental protection policy; procedures addressing physical access control; security plan; physical access control logs or records; inventory records of physical access control devices; system entry and exit points; records of key and lock combination changes; storage locations for physical access control devices; physical access control devices; list of security safeguards controlling access to designated publicly accessible areas within facility; other relevant documents or records].
- Interview: [SELECT FROM: Personnel with physical access control responsibilities; personnel with information security responsibilities
- Test: [SELECT FROM: Organizational processes for physical access control; mechanisms supporting or implementing physical access control; physical access control devices].


### 3.10.5 Control and manage physical access devices.

- Examine: [SELECT FROM: Physical and environmental protection policy; procedures addressing physical access control; security plan; physical access control logs or records; inventory records of physical access control devices; system entry and exit points; records of key and lock combination changes; storage locations for physical access control devices; physical access control devices; list of security safeguards controlling access to designated publicly accessible areas within facility; other relevant documents or records].
- Interview: [SELECT FROM: Personnel with physical access control responsibilities; personnel with information security responsibilities].
- Test: [SELECT FROM: Organizational processes for physical access control; mechanisms supporting or implementing physical access control; physical access control devices].


### 3.10.6 Enforce safeguarding measures for CUI at alternate work sites.

- Examine: [SELECT FROM: Physical and environmental protection policy; procedures addressing alternate work sites for personnel; security plan; list of safeguards required for alternate work sites; assessments of safeguards at alternate work sites; other relevant documents or records].
- Interview: [SELECT FROM: Personnel approving use of alternate work sites; personnel using alternate work sites; personnel assessing controls at alternate work sites; personnel with information security responsibilities].
- Test: [SELECT FROM: Organizational processes for security at alternate work sites; mechanisms supporting alternate work sites; safeguards employed at alternate work sites; means of communications between personnel at alternate work sites and security personnel].


## Risk Assessment


### 3.11.1 Periodically assess the risk to organizational operations (including mission, functions, image, or reputation), organizational assets, and individuals, resulting from the operation of organizational systems and the associated processing, storage, or transmission of CUI

- Examine: [SELECT FROM: Risk assessment policy; security planning policy and procedures; procedures addressing organizational risk assessments; security plan; risk assessment; risk assessment results; risk assessment reviews; risk assessment updates; other relevant documents or records].
- Interview: [SELECT FROM: Personnel with risk assessment responsibilities; personnel with information security responsibilities].
- Test: [SELECT FROM: Organizational processes for risk assessment; mechanisms supporting or for conducting, documenting, reviewing, disseminating, and updating the risk assessment].


### 3.11.2 Scan for vulnerabilities in organizational systems and applications periodically and when new vulnerabilities affecting those systems and applications are identified.

- Examine: [SELECT FROM: Risk assessment policy; procedures addressing vulnerability scanning; risk assessment; security plan; security assessment report; vulnerability scanning tools and associated configuration documentation; vulnerability scanning results; patch and vulnerability management records; other relevant documents or records].
- Interview: [SELECT FROM: Personnel with risk assessment, security assessment and vulnerability scanning responsibilities; personnel with vulnerability scan analysis and remediation responsibilities; personnel with information security responsibilities; system or network administrators].
- Test: [SELECT FROM: Organizational processes for vulnerability scanning, analysis, remediation, and information sharing; mechanisms supporting or implementing vulnerability scanning, analysis, remediation, and information sharing].


### 3.11.3 Remediate vulnerabilities in accordance with risk assessments.

- Examine: [SELECT FROM: Risk assessment policy; procedures addressing vulnerability scanning; risk assessment; security plan; security assessment report; vulnerability scanning tools and associated configuration documentation; vulnerability scanning results; patch and vulnerability management records; other relevant documents or records].
- Interview: [SELECT FROM: Personnel with risk assessment, security assessment and vulnerability scanning responsibilities; personnel with vulnerability scan analysis responsibilities; personnel with vulnerability remediation responsibilities; personnel with information security responsibilities; system or network administrators].
- Test: [SELECT FROM: Organizational processes for vulnerability scanning, analysis, remediation, and information sharing; mechanisms supporting or implementing vulnerability scanning, analysis, remediation, and information sharing].


## Security Assessment


### 3.12.1 Periodically assess the security controls in organizational systems to determine if the controls are effective in their application.

- Examine: [SELECT FROM: Security assessment and authorization policy; procedures addressing security assessment planning; procedures addressing security assessments; security assessment plan; security plan; other relevant documents or records].
- Interview: [SELECT FROM: Personnel with security assessment responsibilities; personnel with information security responsibilities].
- Test: [SELECT FROM: Mechanisms supporting security assessment, security assessment plan development, and security assessment reporting].


### 3.12.2 Develop and implement plans of action designed to correct deficiencies and reduce or eliminate vulnerabilities in organizational systems

- Examine: [SELECT FROM: Security assessment and authorization policy; procedures addressing plan of action; security plan; security assessment plan; security assessment report; security assessment evidence; plan of action; other relevant documents or records].
- Interview: [SELECT FROM: Personnel with plan of action development and implementation responsibilities; personnel with information security responsibilities].
- Test: [SELECT FROM: Mechanisms for developing, implementing, and maintaining plan of action].


### 3.12.3 Monitor security controls on an ongoing basis to ensure the continued effectiveness of the controls.

- Examine: [SELECT FROM: Security planning policy; organizational procedures addressing security plan development and implementation; procedures addressing security plan reviews and updates; enterprise architecture documentation; security plan; records of security plan reviews and updates; other relevant documents or records].
- Interview: [SELECT FROM: Personnel with security planning and plan implementation responsibilities; personnel with information security responsibilities].
- Test: [SELECT FROM: Organizational processes for security plan development, review, update, and approval; mechanisms supporting the security plan].


### 3.12.4 Develop, document, and periodically update system security plans that describe system boundaries, system environments of operation, how security requirements are implemented, and the relationships with or connections to other systems.

- Examine: [SELECT FROM: Security planning policy; procedures addressing security plan development and implementation; procedures addressing security plan reviews and updates; enterprise architecture documentation; security plan; records of security plan reviews and updates; other relevant documents or records].
- Interview: [SELECT FROM: Personnel with security planning and plan implementation responsibilities; personnel with information security responsibilities].
- Test: [SELECT FROM: Organizational processes for security plan development, review, update, and approval; mechanisms supporting the security plan].


## System and Communications Protection


### 3.13.1 Monitor, control, and protect communications (i.e., information transmitted or received by organizational systems) at the external boundaries and key internal boundaries of organizational systems.

- Examine: [SELECT FROM: System and communications protection policy; procedures addressing boundary protection; security plan; list of key internal boundaries of the system; system design documentation; boundary protection hardware and software; enterprise security architecture documentation; system audit logs and records; system configuration settings and associated documentation; other relevant documents or records].
- Interview: [SELECT FROM: System or network administrators; personnel with information security responsibilities; system developer; personnel with boundary protection responsibilities].
- Test: [SELECT FROM: Mechanisms implementing boundary protection capability].


### 3.13.2 Employ architectural designs, software development techniques, and systems engineering principles that promote effective information security within organizational systems.

- Examine: [SELECT FROM: Security planning policy; procedures addressing security plan development and implementation; procedures addressing security plan reviews and updates; enterprise architecture documentation; security plan; records of security plan reviews and updates; other relevant documents or records].
- Interview: [SELECT FROM: Personnel with security planning and plan implementation responsibilities; personnel with information security responsibilities].
- Test: [SELECT FROM: Organizational processes for security plan development, review, update, and approval; mechanisms supporting the system security plan].


### 3.13.3 Separate user functionality from system management functionality.

- Examine: [SELECT FROM: System and communications protection policy; procedures addressing application partitioning; system design documentation; system configuration settings and associated documentation; security plan; system audit logs and records; other relevant documents or records].
- Interview: [SELECT FROM: System or network administrators; personnel with information security responsibilities; system developer].
- Test: [SELECT FROM: Separation of user functionality from system management functionality].


### 3.13.4 Prevent unauthorized and unintended information transfer via shared system resources.

- Examine: [SELECT FROM: System and communications protection policy; procedures addressing application partitioning; security plan; system design documentation; system configuration settings and associated documentation; system audit logs and records; other relevant documents or records].
- Interview: [SELECT FROM: System or network administrators; personnel with information security responsibilities; system developer].
- Test: [SELECT FROM: Separation of user functionality from system management functionality].


### 3.13.5 Implement subnetworks for publicly accessible system components that are physically or logically separated from internal networks.

- Examine: [SELECT FROM: System and communications protection policy; procedures addressing boundary protection; security plan; list of key internal boundaries of the system; system design documentation; boundary protection hardware and software; system configuration settings and associated documentation; enterprise security architecture documentation; system audit logs and records; other relevant documents or records].
- Interview: [SELECT FROM: System or network administrators; personnel with information security responsibilities; system developer; personnel with boundary protection responsibilities].
- Test: [SELECT FROM: Mechanisms implementing boundary protection capability].


### 3.13.6 Deny network communications traffic by default and allow network communications traffic by exception (i.e., deny all, permit by exception).

- Examine: [SELECT FROM: System and communications protection policy; procedures addressing boundary protection; security plan; system design documentation; system configuration settings and associated documentation; system audit logs and records; other relevant documents or records].
- Interview: [SELECT FROM: System or network administrators; personnel with information security responsibilities; system developer; personnel with boundary protection responsibilities].
- Test: [SELECT FROM: Mechanisms implementing traffic management at managed interfaces].


### 3.13.7 Prevent remote devices from simultaneously establishing non-remote connections with organizational systems and communicating via some other connection to resources in external networks (i.e., split tunneling).

- Examine: [SELECT FROM: System and communications protection policy; procedures addressing boundary protection; security plan; system design documentation; system hardware and software; system architecture; system configuration settings and associated documentation; system audit logs and records; other relevant documents or records].
- Interview: [SELECT FROM: System or network administrators; personnel with information security responsibilities; system developer; personnel with boundary protection responsibilities].
- Test: [SELECT FROM: Mechanisms implementing boundary protection capability; mechanisms supporting or restricting non-remote connections].


### 3.13.8 Implement cryptographic mechanisms to prevent unauthorized disclosure of CUI during transmission unless otherwise protected by alternative physical safeguards.

- Examine: [SELECT FROM: System and communications protection policy; procedures addressing transmission confidentiality and integrity; security plan; system design documentation; system configuration settings and associated documentation; system audit logs and records; other relevant documents or records].
- Interview: [SELECT FROM: System or network administrators; personnel with information security responsibilities; system developer].
- Test: [SELECT FROM: Cryptographic mechanisms or mechanisms supporting or implementing transmission confidentiality; organizational processes for defining and implementing alternative physical safeguards].


### 3.13.9 Terminate network connections associated with communications sessions at the end of the sessions or after a defined period of inactivity.

- Examine: [SELECT FROM: System and communications protection policy; procedures addressing network disconnect; system design documentation; security plan; system configuration settings and associated documentation; system audit logs and records; other relevant documents or records].
- Interview: [SELECT FROM: System or network administrators; personnel with information security responsibilities; system developer].
- Test: [SELECT FROM: Mechanisms supporting or implementing network disconnect capability].


### 3.13.10 Establish and manage cryptographic keys for cryptography employed in organizational systems.

- Examine: [SELECT FROM: System and communications protection policy; procedures addressing cryptographic key establishment and management; security plan; system design documentation; cryptographic mechanisms; system configuration settings and associated documentation; system audit logs and records; other relevant documents or records].
- Interview: [SELECT FROM: System or network administrators; personnel with information security responsibilities; personnel with responsibilities for cryptographic key establishment and management].
- Test: [SELECT FROM: Mechanisms supporting or implementing cryptographic key establishment and management].


### 3.13.11 Employ FIPS-validated cryptography when used to protect the confidentiality of CUI.

- Examine: [SELECT FROM: System and communications protection policy; procedures addressing cryptographic protection; security plan; system design documentation; system configuration settings and associated documentation; cryptographic module validation certificates; list of FIPS-validated cryptographic modules; system audit logs and records; other relevant documents or records].
- Interview: [SELECT FROM: System or network administrators; personnel with information security responsibilities; system developer; personnel with responsibilities for cryptographic protection].
- Test: [SELECT FROM: Mechanisms supporting or implementing cryptographic protection].


### 3.13.12 

- Examine: [SELECT FROM: System and communications protection policy; procedures addressing collaborative computing; access control policy and procedures; security plan; system design documentation; system configuration settings and associated documentation; system audit logs and records; other relevant documents or records].
- Interview: [SELECT FROM: System or network administrators; personnel with information security responsibilities; system developer; personnel with responsibilities for managing collaborative computing devices].
- Test: [SELECT FROM: Mechanisms supporting or implementing management of remote activation of collaborative computing devices; mechanisms providing an indication of use of collaborative computing devices].


### 3.13.13 Control and monitor the use of mobile code.

- Examine: [SELECT FROM: System and communications protection policy; procedures addressing mobile code; mobile code usage restrictions, mobile code implementation policy and procedures; security plan; list of acceptable mobile code and mobile code technologies; list of unacceptable mobile code and mobile technologies; authorization records; system monitoring records; system audit logs and records; other relevant documents or records].
- Interview: [SELECT FROM: System or network administrators; personnel with information security responsibilities; personnel with responsibilities for managing mobile code].
- Test: [SELECT FROM: Organizational process for controlling, authorizing, monitoring, and restricting mobile code; mechanisms supporting or implementing the management of mobile code; mechanisms supporting or implementing the monitoring of mobile code].


### 3.13.14 Control and monitor the use of Voice over Internet Protocol (VoIP) technologies

- Examine: [SELECT FROM: System and communications protection policy; procedures addressing VoIP; VoIP usage restrictions; VoIP implementation guidance; security plan; system design documentation; system configuration settings and associated documentation; system monitoring records; system audit logs and records; other relevant documents or records].
- Interview: [SELECT FROM: System or network administrators; personnel with information security responsibilities; personnel with responsibilities for managing VoIP].
- Test: [SELECT FROM: Organizational process for authorizing, monitoring, and controlling VoIP; mechanisms supporting or implementing authorizing, monitoring, and controlling VoIP].


### 3.13.15 Protect the authenticity of communications sessions

- Examine: [SELECT FROM: System and communications protection policy; procedures addressing session authenticity; security plan; system design documentation; system configuration settings and associated documentation; system audit logs and records; other relevant documents or records].
- Interview: [SELECT FROM: System or network administrators; personnel with information security responsibilities].
- Test: [SELECT FROM: Mechanisms supporting or implementing session authenticity].


### 3.13.16 Protect the confidentiality of CUI at rest.

- Examine: [SELECT FROM: System and communications protection policy; procedures addressing protection of information at rest; security plan; system design documentation; list of information at rest requiring confidentiality protections; system configuration settings and associated documentation; cryptographic mechanisms and associated configuration documentation; other relevant documents or records].
- Interview: [SELECT FROM: System or network administrators; personnel with information security responsibilities; system developer].
- Test: [SELECT FROM: Mechanisms supporting or implementing confidentiality protections for information at rest].


## System and Information Integrity


### 3.14.1 Identify, report, and correct system flaws in a timely manner.

- Examine: [SELECT FROM: System and information integrity policy; procedures addressing flaw remediation; procedures addressing configuration management; security plan; list of flaws and vulnerabilities potentially affecting the system; list of recent security flaw remediation actions performed on the system (e.g., list of installed patches, service packs, hot fixes, and other software updates to correct system flaws); test results from the installation of software and firmware updates to correct system flaws; installation/change control records for security-relevant software and firmware updates; other relevant documents or records].
- Interview: [SELECT FROM: System or network administrators; personnel with information security responsibilities; personnel installing, configuring, and maintaining the system; personnel with responsibility for flaw remediation; personnel with configuration management responsibility].
- Test: [SELECT FROM: Organizational processes for identifying, reporting, and correcting system flaws; organizational process for installing software and firmware updates; mechanisms supporting or implementing reporting, and correcting system flaws; mechanisms supporting or implementing testing software and firmware updates].


### 3.14.2 Provide protection from malicious code at designated locations within organizational systems.

- Examine: [SELECT FROM: System and information integrity policy; configuration management policy and procedures; procedures addressing malicious code protection; records of malicious code protection updates; malicious code protection mechanisms; security plan; system design documentation; system configuration settings and associated documentation; record of actions initiated by malicious code protection mechanisms in response to malicious code detection; scan results from malicious code protection mechanisms; system audit logs and records; other relevant documents or records].
- Interview: [SELECT FROM: System or network administrators; personnel with information security responsibilities; personnel installing, configuring, and maintaining the system; personnel with responsibility for malicious code protection; personnel with configuration management responsibility].
- Test: [SELECT FROM: Organizational processes for employing, updating, and configuring malicious code protection mechanisms; organizational process for addressing false positives and resulting potential impact; mechanisms supporting or implementing employing, updating, and configuring malicious code protection mechanisms; mechanisms supporting or implementing malicious code scanning and subsequent actions].


### 3.14.3 Monitor system security alerts and advisories and take action in response.

- Examine: [SELECT FROM: System and information integrity policy; procedures addressing security alerts, advisories, and directives; security plan; records of security alerts and advisories; other relevant documents or records].
- Interview: [SELECT FROM: Personnel with security alert and advisory responsibilities; personnel implementing, operating, maintaining, and using the system; personnel, organizational elements, and external organizations to whom alerts, advisories, and directives are to be disseminated; system or network administrators; personnel with information security responsibilities].
- Test: [SELECT FROM: Organizational processes for defining, receiving, generating, disseminating, and complying with security alerts, advisories, and directives; mechanisms supporting or implementing definition, receipt, generation, and dissemination of security alerts, advisories, and directives; mechanisms supporting or implementing security directives].


### 3.14.4 Update malicious code protection mechanisms when new releases are available.

- Examine: [SELECT FROM: System and information integrity policy; configuration management policy and procedures; procedures addressing malicious code protection; malicious code protection mechanisms; records of malicious code protection updates; security plan; system design documentation; system configuration settings and associated documentation; scan results from malicious code protection mechanisms; record of actions initiated by malicious code protection mechanisms in response to malicious code detection; system audit logs and records; other relevant documents or records].
- Interview: [SELECT FROM: System or network administrators; personnel with information security responsibilities; personnel installing, configuring, and maintaining the system; personnel with responsibility for malicious code protection; personnel with configuration management responsibility].
- Test: [SELECT FROM: Organizational processes for employing, updating, and configuring malicious code protection mechanisms; organizational process for addressing false positives and resulting potential impact; mechanisms supporting or implementing malicious code protection mechanisms (including updates and configurations); mechanisms supporting or implementing malicious code scanning and subsequent actions].


### 3.14.5 Perform periodic scans of organizational systems and real-time scans of files from external sources as files are downloaded, opened, or executed.

- Examine: [SELECT FROM: System and information integrity policy; configuration management policy and procedures; procedures addressing malicious code protection; malicious code protection mechanisms; records of malicious code protection updates; security plan; system design documentation; system configuration settings and associated documentation; scan results from malicious code protection mechanisms; record of actions initiated by malicious code protection mechanisms in response to malicious code detection; system audit logs and records; other relevant documents or records].
- Interview: [SELECT FROM: System or network administrators; personnel with information security responsibilities; personnel installing, configuring, and maintaining the system; personnel with responsibility for malicious code protection; personnel with configuration management responsibility].
- Test: [SELECT FROM: Organizational processes for employing, updating, and configuring malicious code protection mechanisms; organizational process for addressing false positives and resulting potential impact; mechanisms supporting or implementing malicious code protection mechanisms (including updates and configurations); mechanisms supporting or implementing malicious code scanning and subsequent actions].


### 3.14.6 Monitor organizational systems, including inbound and outbound communications traffic, to detect attacks and indicators of potential attacks

- Examine: [SELECT FROM: System and information integrity policy; procedures addressing system monitoring tools and techniques; continuous monitoring strategy; system and information integrity policy; procedures addressing system monitoring tools and techniques; facility diagram or layout; security plan; system design documentation; system monitoring tools and techniques documentation; locations within system where monitoring devices are deployed; system protocols; system configuration settings and associated documentation; system audit logs and records; other relevant documents or records].
- Interview: [SELECT FROM: System or network administrators; personnel with information security responsibilities; personnel installing, configuring, and maintaining the system; personnel with responsibility monitoring the system; personnel with responsibility for the intrusion detection system].
- Test: [SELECT FROM: Organizational processes for system monitoring; mechanisms supporting or implementing intrusion detection capability and system monitoring; mechanisms supporting or implementing system monitoring capability; organizational processes for intrusion detection and system monitoring; mechanisms supporting or implementing the monitoring of inbound and outbound communications traffic].


### 3.14.7 Identify unauthorized use of organizational systems.

- Examine: [SELECT FROM: Continuous monitoring strategy; system and information integrity policy; procedures addressing system monitoring tools and techniques; facility diagram/layout; security plan; system design documentation; system monitoring tools and techniques documentation; locations within system where monitoring devices are deployed; system configuration settings and associated documentation; other relevant documents or records].
- Interview: [SELECT FROM: System or network administrators; personnel with information security responsibilities; personnel installing, configuring, and maintaining the system; personnel with responsibility for monitoring the system].
- Test: [SELECT FROM: Organizational processes for system monitoring; mechanisms supporting or implementing system monitoring capability].


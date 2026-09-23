# NFA WORKFLOW MANAGEMENT SYSTEM
## Master Foundation & Initial Development Prompt

---

# 1. PROJECT OBJECTIVE

We are developing an internal enterprise application called:

**NFA — Note for Approval Workflow Management System**

The purpose of the application is to allow company employees to create, submit, approve, reject, return, and track NFA requests through a controlled workflow.

The system must provide:

- Employee-based user management
- Role-based access
- NFA creation
- Department-wise approver configuration
- Manual and Dynamic approver selection
- Maximum 8 approvers per NFA
- Sequential approval workflow
- Accept / Reject / Return actions
- Configurable Return behavior
- Request revision/version management
- Attachment version management
- Complete approval/workflow history
- Admin configuration
- Auditability
- Secure role-based access

The application must be designed as a scalable enterprise application.

---

# 2. TECHNOLOGY STACK

## Frontend

- React
- TypeScript
- Vite

## Backend

- Python 3.13
- Django
- Django REST Framework

## Database

- Microsoft SQL Server 2022

## Architecture

Frontend and backend must be separate applications communicating through REST APIs.

Do not put important business/workflow logic only in the frontend.

The backend must be the source of truth for workflow decisions, permissions, validation and database operations.

---

# 3. VERY IMPORTANT DEVELOPMENT RULE

Do NOT invent business rules.

Only implement rules explicitly defined in this document.

If a requirement has not yet been decided:

- Do not assume it.
- Do not create an automatic rule.
- Keep the architecture extensible.
- Clearly mark it as an open/future business rule.

Do not make independent business decisions on behalf of the project owner.

---

# 4. EMPLOYEE MASTER

## Purpose

Employee Master represents the complete employee master of the company.

It is the source from which employees are searched and selected.

Employee Master may contain employees who never use the NFA application.

Example:

```text
Employee Master

EMP001 - Rahul
EMP002 - Amit
EMP003 - Neha
EMP004 - Sameer
EMP005 - Karan
...
```

The NFA application should reference employees using their EmployeeID.

Do not unnecessarily duplicate the entire employee master inside the NFA application.

---

# 5. SYSTEM USER

System User represents an employee who participates in the NFA application.

Relationship:

```text
Employee Master
      |
      | EmployeeID
      ↓
System User
```

An employee can exist in Employee Master without being a System User.

A System User must reference the corresponding Employee Master record.

The same EmployeeID must NOT result in duplicate System User records.

---

# 6. USER ROLES

The application initially supports four roles:

1. Buyer
2. Admin
3. Auditor
4. Approver

A System User can have multiple roles.

Example:

```text
Rahul
 ├── Buyer
 └── Approver
```

Another user:

```text
Amit
 ├── Admin
 ├── Buyer
 └── Auditor
```

Another user:

```text
Neha
 └── Approver
```

Therefore use:

```text
User
Role
UserRole
```

Do NOT use fixed columns such as:

```text
IsBuyer
IsAdmin
IsAuditor
IsApprover
```

---

# 7. APPROVER USER MAPPING — CONFIRMED RULE

This is an important confirmed business rule.

When an employee is selected as an Approver:

### Step 1

Search/select the employee from Employee Master.

### Step 2

Check whether the employee already exists in System User.

### Step 3 — If User DOES NOT exist

Create a System User linked to that Employee Master record.

Then assign the Approver role.

### Step 4 — If User ALREADY exists

DO NOT create another User.

Keep the existing System User.

Check whether the user already has the Approver role.

If the Approver role is missing:

**Add the Approver role to the existing User.**

Example:

Before:

```text
Employee Master
Rahul
     ↓
System User
Rahul
     ↓
Buyer
```

Rahul is selected as an Approver.

After:

```text
System User
Rahul
 ├── Buyer
 └── Approver
```

No duplicate System User is created.

If Rahul already has:

```text
Buyer
Approver
```

then nothing additional needs to be created.

---

# 8. DYNAMIC APPROVER — EXACT MEANING

Dynamic Approver does NOT mean automatic calculation.

It does NOT mean:

- Department Head
- Reporting Manager
- Designation
- Seniority
- Approval Level
- Hierarchy
- Salary
- Manager
- Any other employee attribute

Do NOT implement any of those.

For this project:

> **Dynamic Approver means that the user searches and selects an employee directly from Employee Master at the time of NFA creation.**

Flow:

```text
NFA Creation
     ↓
Approver Selection
     ↓
Search Employee Master
     ↓
Select Employee
     ↓
Check System User
     ↓
User exists?
   /       \
 YES       NO
  |         |
  |       Create User
  |         |
  ↓         ↓
Check Approver Role
       ↓
Add Approver Role if required
       ↓
Use Employee as NFA Approver
```

This is the complete Dynamic Approver requirement.

Do not add any additional automatic selection logic.

---

# 9. DEPARTMENT-WISE APPROVER CONFIGURATION

Admin must be able to configure how approvers are selected for each Department.

This configuration is specifically about:

> **WHO becomes the approver / HOW the approver is selected.**

Each department can have an Approver Selection Mode.

Available modes:

### MANUAL APPROVER

Admin manually configures/selects the approver for that department.

### DYNAMIC APPROVER

The approver is selected from Employee Master during NFA creation.

Therefore:

```text
Department
     ↓
Approver Selection Mode
     ↓
 ┌───────────────┐
 │               │
Manual         Dynamic
 │               │
Admin         Employee
configures     Master
approver      selection
```

This configuration must be independent of Return configuration.

---

# 10. MANUAL APPROVER

When a department is configured as:

```text
MANUAL
```

the Admin can configure/select the relevant approver(s) for that department.

The exact UI and number of manually configured approvers can be refined later.

Do not invent additional approval rules.

Any employee configured as an approver must follow the same System User mapping rule:

```text
Employee Master
       ↓
Check System User
       ↓
If missing → Create User
       ↓
Ensure Approver role
```

---

# 11. DYNAMIC APPROVER

When a department is configured as:

```text
DYNAMIC
```

the Buyer can search Employee Master and select the required approver.

There is no automatic employee selection.

The Buyer explicitly selects the employee.

The system then ensures that the selected employee exists as a System User and has the Approver role.

---

# 12. RETURN CONFIGURATION

This is a completely separate Admin configuration.

Do NOT mix Return configuration with Department Approver configuration.

The Return configuration answers:

> **WHERE should the NFA go when an Approver selects Return?**

Admin can configure one of:

### RETURN_TO_INITIATOR

The NFA goes directly to the original Buyer/Initiator.

Example:

```text
Buyer
 ↓
Approver 1
 ↓
Approver 2
 ↓
RETURN
 ↓
Buyer
 ↓
RESUBMIT
 ↓
Approver 2
 ↓
Approver 3
```

After the Buyer resubmits, the workflow resumes from the Approver who returned the NFA.

---

### RETURN_TO_PREVIOUS_APPROVER

The NFA goes back to the immediately previous approver according to the configured workflow.

This is a separate workflow behavior.

---

# 13. TWO INDEPENDENT ADMIN CONFIGURATIONS

The system must clearly separate these:

## Configuration 1 — Department Approver Mode

Determines:

**How/where the approver is selected.**

Options:

```text
MANUAL
DYNAMIC
```

## Configuration 2 — Return Mode

Determines:

**Where the request goes after Return.**

Options:

```text
RETURN_TO_INITIATOR
RETURN_TO_PREVIOUS_APPROVER
```

These configurations must never be treated as the same setting.

---

# 14. NFA REQUEST

Create an NFA Request entity.

It should contain at minimum:

- RequestID
- NFA Number
- Initiator/User
- Department
- Subject/Title
- Estimated Cost
- Business Justification
- Commercial Impact
- Current Status
- Current Approval Position
- Created Date
- Updated Date

The NFA Number must be human-readable and unique.

Example:

```text
NFA-2026-00001
```

---

# 15. NFA CREATION PROCESS

The Buyer creates an NFA in multiple steps.

## STEP 1 — REQUEST DETAILS

Fields:

- Subject / Title
- Department
- Estimated Cost
- Business Justification
- Commercial Impact

Required fields must be validated.

---

## STEP 2 — ATTACHMENTS

The Buyer can upload required documents.

The system must associate attachments with the NFA Request.

---

## STEP 3 — APPROVERS

The system checks the department's configured Approver Selection Mode.

If:

```text
MANUAL
```

use the Admin-configured approver setup.

If:

```text
DYNAMIC
```

allow the Buyer to search/select employees from Employee Master.

Maximum:

**8 approvers per NFA.**

Each approver must have an explicit sequence.

Example:

```text
1 → Amit
2 → Neha
3 → Sameer
4 → Karan
```

---

## STEP 4 — REVIEW

Show the Buyer a complete review of:

- Request information
- Department
- Cost
- Business Justification
- Commercial Impact
- Attachments
- Approver sequence

The Buyer must be able to review the information before submission.

---

## STEP 5 — SUBMIT

After confirmation:

```text
NFA → Submitted
```

The NFA moves to the first approver.

---

# 16. APPROVAL SEQUENCE

Each NFA can contain a maximum of 8 approvers.

Example:

```text
Approver 1
    ↓
Approver 2
    ↓
Approver 3
    ↓
Approver 4
```

The sequence belongs to the individual NFA.

Do not assume that the current Employee Master information will automatically change an already-created NFA approval sequence.

The NFA should retain the approver information associated with that request.

---

# 17. APPROVER ACTIONS

An Approver has three actions:

## ACCEPT

The current approver accepts the NFA.

The NFA moves to the next approver.

If there is no next approver, the NFA becomes:

```text
APPROVED
```

---

## REJECT

The Approver rejects the NFA.

The workflow stops.

Final status:

```text
REJECTED
```

A rejection reason/comment should be captured.

---

## RETURN

The Approver returns the NFA.

The system uses the Admin-configured Return Mode.

The previous history must remain untouched.

---

# 18. RETURN TO INITIATOR — DETAILED BEHAVIOR

If:

```text
Return Mode = RETURN_TO_INITIATOR
```

Example:

```text
Buyer
 ↓
Approver 1
 ↓
Approver 2
 ↓
Approver 3
```

Approver 3 returns the NFA.

The request becomes:

```text
RETURNED
```

The Buyer receives it.

Buyer can modify the permitted information and/or attachments.

Buyer resubmits.

The workflow resumes from:

```text
Approver 3
```

It does NOT automatically restart from Approver 1.

Example:

```text
Approver 1 → Approved
Approver 2 → Approved
Approver 3 → Returned
                  ↓
                Buyer
                  ↓
               Resubmit
                  ↓
              Approver 3
                  ↓
              Approver 4
```

---

# 19. RETURN TO PREVIOUS APPROVER

If:

```text
Return Mode = RETURN_TO_PREVIOUS_APPROVER
```

the request goes to the immediately previous approver according to the configured workflow.

Do not invent additional behavior beyond this requirement.

The workflow must record exactly what happened in history.

---

# 20. REQUEST STATUS

The NFA should maintain a current status.

Initial states may include:

```text
DRAFT
SUBMITTED
PENDING_APPROVAL
RETURNED
REJECTED
APPROVED
```

The backend should control valid state transitions.

Do not allow invalid transitions from the frontend.

---

# 21. WORKFLOW HISTORY

Create a permanent history table associated with RequestID.

Every important workflow action creates a new history record.

Examples:

```text
SUBMITTED
ACCEPTED
REJECTED
RETURNED
RESUBMITTED
```

History should contain information such as:

- HistoryID
- RequestID
- UserID
- EmployeeID
- Approver sequence
- Action
- Previous status
- New status
- Comments
- Action Date/Time
- Workflow cycle/revision where applicable

History must be append-only.

Never overwrite old history.

---

# 22. WORKFLOW CYCLE / REVISION

Returned and resubmitted requests must remain traceable.

Example:

```text
Cycle 1

Buyer → Submit
Approver 1 → Accept
Approver 2 → Accept
Approver 3 → Return
```

Then:

```text
Cycle 2

Buyer → Resubmit
Approver 3 → Accept
Approver 4 → Accept
```

The system should maintain a revision/cycle concept so the complete journey can be reconstructed.

Do not delete Cycle 1.

---

# 23. REQUEST VERSIONING

If a returned NFA is modified, do not simply overwrite the original information without tracking the change.

Maintain request revisions/versions.

Example:

```text
Version 1
Original request
      ↓
Returned
      ↓
Version 2
Updated request
      ↓
Resubmitted
```

The system should allow auditing of what information existed in each revision.

---

# 24. ATTACHMENT VERSIONING

Attachments must also support versions.

Example:

```text
Version 1
quotation.pdf
```

After Return:

```text
Version 2
revised_quotation.pdf
```

Do NOT simply replace the old attachment.

Keep the old attachment record for audit/history.

The system should know which attachment version belongs to which request revision.

---

# 25. CURRENT STATE VS HISTORY

These are different concepts.

## NFARequest

Stores:

> What is happening NOW?

Example:

```text
CurrentStatus = RETURNED
CurrentApproverSequence = 3
```

## NFAApprovalHistory

Stores:

> What has EVER happened?

Example:

```text
Submitted
Approver 1 Accepted
Approver 2 Accepted
Approver 3 Returned
Buyer Resubmitted
Approver 3 Accepted
```

Never use the current status as a replacement for history.

---

# 26. ADMIN MODULE

The Admin will eventually manage/configure:

### Users

View/manage System Users.

### Roles

Assign/remove roles.

### Departments

Manage departments as required.

### Department Approver Configuration

Configure:

```text
Department → MANUAL / DYNAMIC
```

### Manual Approver Configuration

Configure approvers where Manual mode is used.

### Return Configuration

Configure:

```text
RETURN_TO_INITIATOR
```

or:

```text
RETURN_TO_PREVIOUS_APPROVER
```

---

# 27. AUDITOR ROLE

Auditor is a separate role.

Auditor should eventually have access to appropriate NFA history/audit information.

Do not assume specific Auditor permissions beyond the need to support an Auditor role.

The exact Auditor screen and permissions can be defined later.

---

# 28. BUYER ROLE

Buyer is responsible for initiating NFA requests.

Buyer functionality will eventually include:

- Create NFA
- Save draft
- Upload attachments
- Select approvers where applicable
- Review
- Submit
- View own NFA requests
- Act on returned requests
- Modify and resubmit returned requests

Do not invent additional Buyer capabilities.

---

# 29. APPROVER ROLE

Approver functionality will eventually include:

- View assigned NFA requests
- View complete NFA details
- View relevant attachments
- Accept
- Reject
- Return
- Provide comments/reasons where required

---

# 30. ROLE-BASED ACCESS

The frontend should show navigation according to the user's roles.

However, frontend hiding is NOT sufficient.

Backend APIs must also enforce authorization.

For example:

A Buyer must not be able to call an Admin API simply by manually entering the API URL.

A user must not be able to access an NFA they are not authorized to access simply by changing RequestID.

---

# 31. DATABASE CORE ENTITIES

Create the initial database architecture around:

```text
EmployeeMaster
User
Role
UserRole
Department

NFARequest
NFARequestVersion

NFAApprover
NFAApprovalHistory

NFAAttachment
NFAAttachmentVersion

DepartmentApproverConfiguration
ManualApproverConfiguration

WorkflowConfiguration
```

Additional tables may be introduced only when justified by an explicit requirement.

Do not unnecessarily over-engineer the database.

---

# 32. IMPORTANT DATABASE RELATIONSHIPS

At a high level:

```text
EmployeeMaster
      ↓
     User
      ↓
   UserRole
      ↓
     Role
```

NFA:

```text
User
 ↓
NFARequest
 ↓
 ├── NFARequestVersion
 ├── NFAApprover
 ├── NFAAttachment
 └── NFAApprovalHistory
```

Department:

```text
Department
    ↓
DepartmentApproverConfiguration
    ↓
MANUAL / DYNAMIC
```

Workflow:

```text
WorkflowConfiguration
        ↓
Return Mode
        ↓
Initiator / Previous Approver
```

---

# 33. DATA INTEGRITY

Implement appropriate:

- Primary keys
- Foreign keys
- Unique constraints
- Indexes
- Required fields
- Referential integrity

Particularly ensure:

```text
One EmployeeID → Maximum One System User
```

and:

```text
One User + One Role → One UserRole mapping
```

Do not create duplicate mappings.

---

# 34. BACKEND WORKFLOW SERVICE

Create a dedicated backend workflow/service layer.

Workflow operations should include concepts such as:

```text
submit_nfa()
accept_nfa()
reject_nfa()
return_nfa()
resubmit_nfa()
get_next_approver()
```

The exact implementation can differ, but workflow logic should be centralized rather than duplicated across API views.

---

# 35. TRANSACTION SAFETY

Operations involving multiple database changes should be transactional.

For example, when an employee is selected as a Dynamic Approver:

```text
Check User
   ↓
Create User if required
   ↓
Ensure Approver Role
   ↓
Create NFA Approver mapping
```

These related operations should be handled safely so that the database does not end up in an inconsistent state.

---

# 36. UI FOUNDATION

Create a professional enterprise UI foundation.

Initially create:

### Login

- Username/email
- Password
- Login button
- Error handling

### Application Layout

- Header
- Sidebar
- Main content
- User profile/menu

### Dashboard placeholders

Buyer Dashboard

Admin Dashboard

Approver Dashboard

Auditor Dashboard

Navigation should be role-aware.

Do not build all detailed modules during the foundation phase.

---

# 37. API FOUNDATION

Create REST API architecture for:

- Authentication
- Users
- Roles
- Employee Master lookup
- Departments
- NFA Requests
- Approvers
- Attachments
- History
- Admin configurations

Use consistent API naming and error responses.

---

# 38. EMPLOYEE SEARCH

The application must provide employee search from Employee Master.

For Dynamic Approver selection:

```text
Search Employee
      ↓
Employee Master results
      ↓
Select Employee
```

Do not search an independent copied employee list for Dynamic Approver selection.

Employee Master is the source.

---

# 39. NO DUPLICATE USER CREATION

This rule is mandatory.

Example:

Rahul exists in Employee Master.

Rahul does not exist in System User.

Buyer selects Rahul as Approver.

System:

```text
Create Rahul as System User
Add Approver role
```

Later another NFA selects Rahul.

System:

```text
Find Rahul by EmployeeID
User already exists
Do NOT create another User
Ensure Approver role exists
Use existing User
```

If Rahul already has Buyer:

```text
Buyer
```

after being selected as Approver:

```text
Buyer
Approver
```

The existing Buyer role must NOT be removed.

---

# 40. FUTURE EXTENSIBILITY

The architecture should allow future additions such as:

- Additional roles
- Additional Return modes
- Additional department configuration
- Additional workflow actions
- Approval delegation
- Notifications
- Email notifications
- Dashboard/reporting
- Advanced audit reporting

However, do NOT implement these unless specifically requested.

---

# 41. FIRST DEVELOPMENT PHASE

For the first development phase, build only the foundation.

Deliver:

1. React + TypeScript + Vite project
2. Django + DRF project
3. SQL Server 2022 connection
4. Proper frontend/backend folder structure
5. Environment configuration
6. Django models
7. Database relationships
8. Initial migrations
9. Authentication foundation
10. User model
11. Role model
12. UserRole model
13. Employee Master integration/model structure
14. Department model
15. Department Approver Configuration
16. Workflow/Return Configuration
17. Basic REST API structure
18. Backend permission foundation
19. Frontend application shell
20. Role-aware navigation
21. Basic dashboard placeholders
22. Employee search foundation
23. Development seed data
24. README with complete setup instructions

---

# 42. DO NOT BUILD EVERYTHING AT ONCE

This is a staged project.

For this first phase:

**DO NOT fully implement the entire NFA workflow yet.**

First make sure:

- Application starts
- Frontend communicates with backend
- Backend communicates with SQL Server
- Database migrations work
- Authentication foundation works
- User/Role relationships work
- Employee Master relationship works
- Department configuration structure works
- Return configuration structure works
- Basic UI works
- APIs work
- Authorization foundation works

Only after this foundation is stable should the next NFA module be implemented.

---

# 43. DEVELOPMENT APPROACH

Build the application module-by-module.

After completing each module:

1. Run the application.
2. Test the database.
3. Test the API.
4. Test the frontend.
5. Check relationships.
6. Check permissions.
7. Fix errors.
8. Only then proceed to the next module.

Do not silently rewrite previously working architecture.

If a future requirement requires a database/design change, clearly explain:

- What needs to change
- Why it needs to change
- Which existing modules are affected

Then implement the change carefully.

---

# 44. CURRENT OPEN BUSINESS RULES

The following are intentionally NOT defined yet and must NOT be assumed:

- Exact permissions for every Auditor action
- Exact fields editable after Return
- Whether Buyer can change the approver list after Return
- Exact behavior of Return to Previous Approver after the previous approver receives it
- Notification/email rules
- Authentication provider/integration details
- Employee Master integration mechanism/API
- Exact Manual Approver configuration UI
- Additional future workflow rules

Keep the architecture flexible for these decisions.

---

# 45. FINAL INSTRUCTION TO ANTIGRAVITY

Start by creating the complete technical foundation described above.

Do not invent missing business rules.

Do not implement automatic approver selection based on designation, hierarchy, reporting manager, department head or any employee attribute.

For Dynamic Approver:

**Employee Master → User searches/selects employee → Check System User → Create if missing → Ensure Approver role → Use existing/new User as Approver.**

If the employee already exists as a System User with another role such as Buyer:

**Keep the existing User and ADD the Approver role.**

Do not create a duplicate User.

For Department configuration:

**Admin decides MANUAL or DYNAMIC approver selection.**

For Return configuration:

**Admin independently decides RETURN_TO_INITIATOR or RETURN_TO_PREVIOUS_APPROVER.**

Do not mix these two configurations.

Build a clean, maintainable, scalable foundation first.

Do not proceed into unconfirmed business functionality until the foundation is successfully running.
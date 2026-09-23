# NFA WORKFLOW MANAGEMENT SYSTEM
## Technical Requirements & Design Document

**Project:** NFA — Note for Approval Workflow Management System  
**Document Type:** Technical Requirements & Design Document  
**Version:** 1.0  
**Status:** Draft for Technical Review

---

# 1. Purpose of This Document

This document translates the approved Business Requirements Document (BRD) into the technical requirements and architecture required to develop the NFA application.

The BRD defines:

> **WHAT the business wants the system to do.**

This document defines:

> **HOW the application should technically support those requirements.**

This document must not introduce new business rules without explicit confirmation.

Where a technical implementation detail has not yet been specified, it is marked as:

**TBD / Technical Decision Required**

or

**Technical Recommendation**

rather than being treated as an approved business requirement.

---

# 2. Confirmed Technology Stack

The application will use:

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

## Communication

Frontend and backend will communicate through REST APIs.

---

# 3. High-Level System Architecture

The proposed architecture is:

```text
                    NFA APPLICATION
                          |
             +------------+------------+
             |                         |
             ↓                         ↓
       FRONTEND                    BACKEND
   React + TypeScript          Django + DRF
        + Vite                     |
             |                     |
             +----------API--------+
                       |
                       ↓
                SQL Server 2022
```

The frontend is responsible primarily for:

- User interface
- User interaction
- Form presentation
- Client-side validation where appropriate
- Displaying API responses
- Navigation

The backend is responsible for:

- Authentication
- Authorization
- Business workflow
- Validation
- Database operations
- Approval processing
- Return processing
- History
- Revision management
- Attachment management
- Notifications
- Security

The backend must remain the authoritative source for workflow decisions.

---

# 4. Application Architecture Principles

The application should follow these principles:

### 4.1 Separation of Concerns

Frontend, backend, database and workflow logic should remain properly separated.

### 4.2 Backend-Controlled Workflow

Important workflow decisions must not depend only on frontend logic.

### 4.3 Role-Based Authorization

The backend must verify that a user is authorized to perform an operation.

### 4.4 Auditability

Important actions must create historical records rather than silently overwriting previous information.

### 4.5 Extensibility

The architecture should allow future changes without requiring a complete redesign.

### 4.6 No Unconfirmed Business Logic

Technical implementation must not introduce assumptions about business behavior.

---

# 5. Core Technical Modules

The application should be organized into logical modules.

Initial modules:

1. Authentication
2. User Management
3. Role Management
4. Employee Master
5. Department Management
6. Department Approver Configuration
7. Workflow Configuration
8. NFA Management
9. Approver Management
10. Attachment Management
11. Workflow History
12. Notifications
13. Auditor Access
14. Dashboard/Reporting

The exact Django app/module structure can be finalized during implementation.

---

# 6. Employee Master Architecture

Employee Master is the source of employee information used by the NFA application.

Initially, employee data will be maintained manually.

There is currently no external Employee Master integration.

The technical model should therefore support an Employee Master table/entity.

At minimum, the relationship should support:

```text
EmployeeMaster
      |
      | EmployeeID
      ↓
SystemUser
```

Employee Master should not be duplicated unnecessarily in other tables.

---

# 7. System User Architecture

System User represents an employee who participates in the NFA system.

A System User must reference an Employee Master employee.

The system must prevent duplicate System User mappings for the same EmployeeID.

Conceptually:

```text
EmployeeMaster
----------------
EmployeeID PK
Employee information
        |
        | 1 : 0..1
        ↓
SystemUser
----------------
UserID PK
EmployeeID FK
Authentication-related information
Status
```

The exact Employee Master fields are currently not finalized.

---

# 8. Role Architecture

Roles:

- Buyer
- Admin
- Approver
- Auditor

A System User can have multiple roles.

Technical relationship:

```text
User
 |
 +---- UserRole ---- Role
 |
 +---- UserRole ---- Role
 |
 +---- UserRole ---- Role
```

The system should prevent duplicate User/Role mappings.

Existing roles must not be removed when another role is added.

---

# 9. Approver User Provisioning

When an employee is selected as an Approver:

```text
Employee Master
       ↓
Selected Employee
       ↓
Check System User
       ↓
User exists?
   /         \
 YES         NO
 |            |
 |          Create User
 |            |
 +------┬-----+
        ↓
Check Approver Role
        ↓
Add role if missing
        ↓
Use System User
```

### Confirmed rule

If Rahul already exists as:

```text
Rahul
 └── Buyer
```

and Rahul is selected as an Approver:

```text
Rahul
 ├── Buyer
 └── Approver
```

The system must not create another User.

If Rahul already has Approver:

```text
Rahul
 ├── Buyer
 └── Approver
```

no additional role mapping is required.

---

# 10. Authentication Architecture

Two authentication modes are required:

- LOCAL
- AD

The exact authentication implementation must keep these modes independently configurable.

---

# 11. Local Authentication

Flow:

```text
Login
  ↓
User enters credentials
  ↓
Backend validates against local authentication data
  ↓
Valid?
 ├── YES → Authentication success → Dashboard
 └── NO  → Login page + error
```

The application must not expose password data to the frontend beyond what is required for authentication.

Password storage must follow secure password-storage practices.

The exact password policy is currently TBD.

---

# 12. AD Authentication

The AD URL will be provided/configured later.

The required business flow is:

```text
Login
  ↓
User Alias + Password
  ↓
Configured AD URL
  ↓
AD response
  ↓
isSuccess?
 ├── true  → Dashboard
 └── false → Remain on Login
```

The AD URL must be configuration-driven rather than hard-coded.

The exact request format and response schema from the AD endpoint are TBD until the AD interface is provided.

The application should therefore isolate AD authentication behind an authentication service/interface so that the final endpoint details can be added later.

---

# 13. Authentication Mode Configuration

The application should support configuration of the authentication mode:

```text
LOCAL
AD
```

Only the configured authentication method should be used for the applicable login flow.

The exact mechanism for changing the mode has not yet been specified.

**TBD:** Whether authentication mode can be changed through an Admin UI or only through application configuration/environment settings.

---

# 14. Department Architecture

Departments will be manually maintained by Admin.

Technical structure should support:

```text
Department
------------
DepartmentID
DepartmentName
Status
```

The exact additional Department fields are TBD.

Departments are used for:

- NFA request selection
- Department-wise approver configuration
- Auditor filtering

---

# 15. Department Approver Configuration

Admin can configure the Approver selection mode for each Department.

Available modes:

```text
MANUAL
DYNAMIC
```

Conceptually:

```text
Department
     ↓
Department Approver Configuration
     ↓
Approver Mode
   /       \
Manual    Dynamic
```

This configuration is independent of Return configuration.

---

# 16. Manual Approver Configuration

When a Department is configured as Manual:

Admin can configure multiple Approvers.

Admin will also determine their sequence/order.

Example:

```text
Department: Finance

1 → Rahul
2 → Amit
3 → Neha
4 → Sameer
```

The technical design must preserve the configured order.

The exact behavior when the Department's manual configuration is changed after existing NFAs have already been created must be handled so that existing NFA approval workflows are not unintentionally changed.

**Technical recommendation:** Existing submitted NFA approval sequences should be treated independently from future Department configuration changes.

This is a technical protection against historical workflow changes and does not introduce a new business rule.

---

# 17. Dynamic Approver Configuration

When a Department is configured as Dynamic:

The Buyer can search Employee Master and select Approvers directly.

There are no restrictions on which Employee Master employee can be selected.

The Buyer can select any number of Approvers up to the maximum of 8.

Flow:

```text
Buyer
 ↓
Search Employee Master
 ↓
Select Employee
 ↓
Check System User
 ↓
Create User if required
 ↓
Ensure Approver Role
 ↓
Add to NFA Approver List
```

There is no automatic designation, hierarchy, reporting-manager or department-head logic.

---

# 18. NFA Approver Structure

Each submitted NFA has its own approval sequence.

The technical structure should support:

```text
NFA Request
     |
     +--- Approver 1
     +--- Approver 2
     +--- Approver 3
     ...
     +--- Approver 8
```

Each approver record should be associated with:

- Request
- User/employee
- Sequence
- Workflow status
- Relevant action information

The exact final column design will be defined during ERD/database design.

---

# 19. Maximum Approvers

The maximum number of Approvers associated with one NFA is:

**8**

The backend must enforce this limit.

The frontend should also provide an appropriate user experience preventing selection beyond the allowed limit.

Backend enforcement remains authoritative.

---

# 20. Approver List Locking

Once an NFA has been submitted:

**The Approver list cannot be changed by the Buyer.**

This remains true after the NFA is returned.

The technical implementation should therefore prevent Buyer APIs from modifying the submitted NFA's approver list.

Any future administrative capability to change an approval workflow would require an explicitly defined business requirement.

---

# 21. NFA Request Architecture

The NFA Request is the central workflow entity.

Conceptually:

```text
NFARequest
------------
RequestID
NFA Number
Initiator
Department
Subject
Estimated Cost
Business Justification
Commercial Impact
Current Status
Current Workflow Position
Created Date
Updated Date
```

Exact field types and constraints will be defined in the ERD.

---

# 22. NFA Creation Architecture

The frontend should provide a structured multi-step creation process:

```text
Request Details
      ↓
Attachments
      ↓
Approvers
      ↓
Review
      ↓
Submit
```

The system must preserve entered information as the Buyer progresses through the creation process.

---

# 23. Draft Architecture

Buyer can save an incomplete NFA as Draft.

A Draft:

- Has not entered approval workflow.
- Can be reopened.
- Can be modified.
- Can be completed.
- Can be submitted later.

---

# 24. Draft Deletion

Draft deletion will be implemented as a **soft delete**.

The physical database record should not be permanently deleted as part of normal Buyer Draft deletion.

The deletion event must remain traceable through history/audit information.

Conceptually:

```text
Draft
 ↓
Delete
 ↓
Soft Deleted
```

rather than:

```text
Draft
 ↓
Physical DELETE
```

The exact visibility rules for soft-deleted drafts are a technical/UI detail to be finalized during implementation.

---

# 25. NFA Submission

When a Buyer submits an NFA:

1. Validate required information.
2. Validate attachment requirements applicable to the request.
3. Validate the approval list.
4. Validate that the NFA has no more than 8 approvers.
5. Lock the submitted approval list against Buyer modification.
6. Create the required workflow/history record.
7. Set the appropriate current status.
8. Identify the first Approver.
9. Trigger applicable notification processing.

The exact initial status names will be finalized in the workflow state design.

---

# 26. Approval Workflow

The workflow is sequential.

Example:

```text
Buyer
 ↓
A1
 ↓
A2
 ↓
A3
 ↓
A4
```

A1 must process the NFA before A2 can process it.

A2 must process it before A3.

The backend must determine the currently active Approver.

---

# 27. Accept

When the current Approver accepts:

```text
Current Approver
      ↓
ACCEPT
      ↓
Next Approver
```

If there is another Approver, the NFA moves to that Approver.

If the current Approver is the final Approver and accepts:

```text
Final Approver
      ↓
ACCEPT
      ↓
APPROVED
```

---

# 28. Reject

When an Approver rejects:

```text
Current Approver
      ↓
REJECT
      ↓
REJECTED
```

Rejected is final according to the confirmed business requirement.

Admin cannot reopen a rejected NFA.

A rejection action must create a history record.

---

# 29. Return Configuration Architecture

Return configuration is independent from Department Approver configuration.

The system supports:

```text
RETURN_TO_INITIATOR
RETURN_TO_PREVIOUS_APPROVER
```

Conceptually:

```text
Workflow Configuration
          ↓
      Return Mode
       /       \
 Initiator   Previous
             Approver
```

---

# 30. Return to Initiator

If Return Mode is:

```text
RETURN_TO_INITIATOR
```

and:

```text
Buyer → A1 → A2 → A3
```

A3 returns:

```text
A3
 ↓ Return
Buyer
```

The Buyer can modify the overall NFA information and attachments.

The Approver list cannot be changed.

After resubmission, the workflow resumes from the Approver who returned the NFA.

Example:

```text
A1 → Approved
A2 → Approved
A3 → Returned
       ↓
     Buyer
       ↓
   Resubmit
       ↓
      A3
```

---

# 31. Return to Previous Approver — Confirmed Behavior

The confirmed Return-to-Previous-Approver behavior is:

> The NFA moves backward through the approval chain one Approver at a time until it reaches the Initiator/Buyer.

Example:

```text
Buyer
  ↓
A1
  ↓
A2
  ↓
A3
```

If A3 returns:

```text
A3
 ↓
A2
 ↓
A1
 ↓
Buyer
```

Therefore this mode is effectively a **backward traversal through the existing approval sequence**.

The technical implementation must record each Return action separately in history.

---

# 32. Important Open Point After Backward Return

The business requirement currently defines how the NFA moves backward:

```text
A3 → A2 → A1 → Buyer
```

However, the exact behavior of the workflow **after the Buyer resubmits** following this backward traversal has not yet been defined.

This must NOT be assumed.

It should be finalized during detailed Workflow State Design.

Until confirmed, the technical architecture should support this scenario without hard-coding an unapproved resubmission behavior.

---

# 33. Returned NFA Editing

After Return, the Buyer can modify the overall NFA information.

The confirmed requirement is:

> The Buyer can edit the overall NFA.

The Approver list remains locked.

The technical design must therefore distinguish between:

```text
Editable NFA data
```

and:

```text
Locked approval sequence
```

---

# 34. Request Versioning

Returned NFA modifications must not destroy the previous request information.

The technical design should support request revisions.

Conceptually:

```text
NFA Request
   |
   +--- Version 1
   |
   +--- Version 2
   |
   +--- Version 3
```

Each revision should be traceable to the Request ID.

The exact version-numbering mechanism will be finalized during database design.

---

# 35. Attachment Architecture

Attachments should be stored separately from the core NFA Request record.

Conceptually:

```text
NFA Request
     |
     +--- Attachment
             |
             +--- Version 1
             +--- Version 2
             +--- Version 3
```

If the Buyer changes an attachment after Return:

```text
Original File
     ↓
Retained
     ↓
New Attachment Version
```

The previous attachment must not simply be overwritten.

---

# 36. File Storage

The BRD confirms attachment management but does not yet specify where physical files will be stored.

Therefore the following is currently:

**TBD**

Possible storage approaches may include:

- Application server storage
- Network storage
- Database binary storage
- Object storage

No storage mechanism should be treated as approved until this is decided.

The database should store appropriate attachment metadata independently of the eventual physical storage mechanism.

---

# 37. History Architecture

Workflow history must be append-only.

Conceptually:

```text
NFA
 |
 +--- History 1: Submitted
 +--- History 2: A1 Accepted
 +--- History 3: A2 Accepted
 +--- History 4: A3 Returned
 +--- History 5: Buyer Resubmitted
```

Existing history records must not be overwritten.

History should support:

- Request ID
- User
- Employee
- Approver sequence
- Action
- Previous status
- New status
- Comments
- Timestamp
- Workflow cycle/revision

Exact schema will be finalized in ERD design.

---

# 38. Workflow Cycle

Because a request can be returned and resubmitted multiple times, the system should support a workflow cycle/revision concept.

Example:

```text
Cycle 1
Buyer → A1 → A2 → A3 → Return

Cycle 2
Buyer → A3 → A4 → Approved
```

The exact cycle numbering mechanism will be finalized during workflow/database design.

---

# 39. Current State vs History

The system must distinguish:

### Current State

Stored on the NFA Request.

Example:

```text
Status = PENDING_APPROVAL
CurrentApprover = A3
```

### Historical State

Stored in the History records.

Example:

```text
Submitted
A1 Accepted
A2 Accepted
A3 Returned
Buyer Resubmitted
```

Current state can change.

History must remain.

---

# 40. Notifications

The application will support:

- In-app notifications
- Email notifications

Notifications are required for relevant workflow events.

The exact notification events, templates and timing have not yet been finalized.

Therefore the notification architecture should be designed as a separate service/module capable of receiving workflow events.

The final notification matrix will be defined later.

---

# 41. Auditor Architecture

Auditor functionality is restricted to viewing:

**Approved NFAs**

The Auditor will select a Department from a Department dropdown.

The system will return Approved NFAs associated with the selected Department.

The Auditor does not perform approval workflow actions according to the current requirement.

---

# 42. Role/Page/Action Architecture

The application must internally associate functionality with roles.

The technical model should support:

```text
Role
  ↓
Permission
  ↓
Page / Feature / Action
```

This allows a user with multiple roles to access the appropriate functionality from all assigned roles.

Example:

```text
User
 ├── Buyer
 └── Approver
```

The system can therefore provide access to both Buyer and Approver functionality according to the permission model.

The exact permission matrix will be finalized from the approved role requirements.

---

# 43. UI/UX Technical Requirements

The application must provide a premium enterprise experience.

Confirmed design direction:

### Overall Style

**Apple-like premium experience**

The goal is:

- Clean
- Minimal
- Smooth
- Premium
- Fast-feeling
- Consistent
- Professional

This does not mean copying Apple's UI.

It means applying similar principles of:

- Simplicity
- Visual hierarchy
- Consistency
- Responsive interactions
- Attention to detail

---

# 44. Theme

The application will be:

**Light-first**

The primary interface should use a clean light visual system.

The exact:

- Color palette
- Brand colors
- Logo
- Typography

will be finalized when branding information is provided.

Do not invent company branding.

---

# 45. Dashboard Design

The Dashboard should follow an **enterprise dashboard** approach while maintaining the premium visual style.

It should prioritize useful information such as applicable:

- NFA status
- Pending actions
- Recent requests
- Approval activity
- Department information
- Other role-specific information

The exact dashboard metrics are not yet finalized.

Do not invent KPI requirements.

---

# 46. Navigation

Navigation must be role-aware.

The application should internally understand which pages/features/actions belong to which roles.

A user with multiple roles should receive the appropriate functionality for all assigned roles.

The exact navigation grouping can be finalized during UI implementation.

---

# 47. Interaction and Animation

Animations should be:

**Subtle and premium.**

Appropriate examples include:

- Smooth transitions
- Button interaction feedback
- Modal transitions
- Dropdown transitions
- Loading states
- Skeleton loading where useful
- Smooth status changes
- Toast notifications

Avoid unnecessary or excessive animations.

The goal is:

> Smooth and responsive rather than animated for the sake of animation.

---

# 48. Responsive Design

The application should be designed responsively.

The exact supported screen/device requirements have not yet been specified.

At minimum, the UI architecture should avoid hard-coded dimensions that prevent future responsive support.

The exact responsive breakpoint strategy can be finalized during UI implementation.

---

# 49. API Architecture

Frontend communication with the backend should use REST APIs.

The API structure should be logically separated by domain.

Potential domains include:

```text
Authentication
Users
Roles
Employees
Departments
Approver Configuration
NFA
Approvers
Attachments
History
Notifications
Auditor
```

The exact endpoint naming and request/response schemas will be finalized during API Design.

---

# 50. Backend Service Architecture

Workflow operations should be implemented in a dedicated service/business layer rather than being duplicated across individual API views.

Examples of workflow operations include:

```text
Create NFA
Save Draft
Submit NFA
Accept NFA
Reject NFA
Return NFA
Resubmit NFA
```

The exact service implementation will be determined during development.

---

# 51. Database Integrity

The database should enforce appropriate integrity constraints.

Important confirmed constraints include:

### Employee → User

One EmployeeID should not create multiple System User mappings.

### User → Role

The same User/Role combination should not be duplicated.

### NFA → Approvers

One NFA cannot contain more than 8 Approvers.

### NFA → History

History records must remain associated with the correct Request ID.

---

# 52. Transaction Safety

Operations that modify multiple related entities should be performed transactionally where required.

Example:

Dynamic Approver selection:

```text
Select Employee
      ↓
Check User
      ↓
Create User if needed
      ↓
Add Approver Role if needed
      ↓
Create NFA Approver mapping
```

The system should avoid leaving partially completed mappings if a database operation fails.

---

# 53. Security Requirements

The backend must enforce authorization.

The system must not rely solely on frontend page hiding.

Examples:

A Buyer should not be able to access Admin functionality simply by manually calling an Admin API.

A user should not be able to access an unauthorized NFA by changing a Request ID.

Approvers should only be able to perform approval actions on requests they are currently authorized to process.

The exact security implementation will be finalized during development.

---

# 54. Error Handling

The application should provide consistent error handling across frontend and backend.

Errors should be:

- Understandable to users
- Logged appropriately on the backend
- Returned through consistent API responses
- Preventing accidental duplicate submissions where applicable

Technical error details should not unnecessarily be exposed to end users.

---

# 55. Logging

The application should maintain technical logs for debugging and operational purposes.

Technical logging is different from NFA business history.

### Business History

Records:

> Rahul approved NFA-001.

### Technical Log

Records:

> API request failed due to database connection issue.

These must remain separate concepts.

---

# 56. Proposed Core Database Entities

Based on the approved requirements, the technical design should initially support:

```text
EmployeeMaster
User
Role
UserRole

Department

DepartmentApproverConfiguration
ManualApproverConfiguration

WorkflowConfiguration

NFARequest
NFARequestVersion
NFAApprover
NFAApprovalHistory

NFAAttachment
NFAAttachmentVersion

Notification
```

Additional technical tables may be required during detailed ERD design.

Any additional table should have a clear technical justification.

---

# 57. Database Design Phase

The next technical activity after this document is to produce the detailed ERD.

The ERD should define:

- Tables
- Columns
- Data types
- Primary keys
- Foreign keys
- Unique constraints
- Indexes
- Cardinality
- Relationships

The ERD must be derived from this document and the BRD.

---

# 58. Workflow State Design Phase

After the ERD, the workflow state machine should be formally defined.

It must cover:

```text
Draft
Submitted
Pending Approval
Approved
Rejected
Returned
Resubmitted
```

and the transitions between them.

Special attention is required for:

- Return to Initiator
- Backward Return to Previous Approver
- Resubmission
- Multiple Return cycles
- Final approval
- Final rejection

No unconfirmed transition should be invented.

---

# 59. API Design Phase

After the workflow design, the API contract should be defined.

The API document should specify:

- Endpoint
- HTTP method
- Authentication requirement
- Permission requirement
- Request structure
- Response structure
- Validation
- Error responses

This will allow React and Django development to proceed consistently.

---

# 60. UI/UX Design Phase

After the technical architecture is finalized, detailed UI/UX specifications should be prepared for:

- Login
- Dashboard
- NFA creation
- Drafts
- Attachments
- Approver selection
- Review
- Approver dashboard
- Approval details
- Return workflow
- Admin configuration
- Auditor view
- Notifications
- History/timeline

The design should follow the confirmed:

**Premium + Light-first + Enterprise + Smooth/Subtle interaction**

direction.

---

# 61. Items Explicitly NOT Assumed

The following are intentionally not decided in this Technical Design:

- Exact Employee Master fields
- Exact AD request format
- Exact AD response schema beyond `isSuccess`
- Exact AD URL
- Password policy
- Password reset mechanism
- Exact notification templates
- Exact notification timing
- Exact attachment storage location
- Exact attachment file limits
- Exact Auditor permissions beyond current requirement
- Exact post-resubmission behavior after backward Return
- Exact responsive breakpoints
- Exact company branding
- Exact dashboard KPIs
- Deployment environment
- Additional external integrations

These remain open and will be finalized when required.

---

# 62. Technical Design Development Sequence

The project should proceed in this order:

```text
BRD
  ↓
Technical Requirements & Design
  ↓
ERD / Database Design
  ↓
Workflow State Machine
  ↓
API Design
  ↓
UI/UX Detailed Design
  ↓
Final Antigravity Foundation Prompt
  ↓
Foundation Development
  ↓
Module-by-Module Development
```

---

# 63. Development Principle

The application should not be generated as one uncontrolled large implementation.

Development should proceed module-by-module.

Each module should be:

1. Designed
2. Implemented
3. Tested
4. Reviewed
5. Corrected
6. Integrated

before moving to the next major module.

---

# 64. Current Technical Status

### Confirmed

- React + TypeScript + Vite
- Django + Django REST Framework
- Python 3.13
- SQL Server 2022
- Local authentication
- AD authentication
- Manual Employee Master
- Multi-role User architecture
- Employee → System User mapping
- Approver role provisioning
- Department management
- Manual/Dynamic Approver modes
- Maximum 8 Approvers
- Admin-defined Manual Approver sequence
- Dynamic Employee Master selection
- Locked Approver list after submission
- Draft + soft deletion
- Accept / Reject / Return
- Return to Initiator
- Backward Return to Previous Approver
- Request revision
- Attachment versioning
- Workflow history
- Notifications
- Auditor approved-NFA view by Department
- Premium Light-first UI
- Enterprise dashboard
- Subtle animations

### Still Open

Only requirements explicitly marked TBD in this document remain open.

They should be resolved when the relevant implementation stage is reached.

---

# 65. Final Technical Principle

The technical design must follow this rule:

> **Implement what has been confirmed. Make unconfirmed areas configurable/extensible. Never invent a business rule and present it as an approved requirement.**

The Technical Design Document, BRD and future ERD/workflow documents should remain aligned.

Any future requirement change should identify:

- What is changing
- Why it is changing
- Which technical components are affected
- Whether the database/API/workflow needs modification

This will prevent uncontrolled changes during development.
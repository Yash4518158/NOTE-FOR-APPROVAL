# NFA WORKFLOW MANAGEMENT SYSTEM
## Business Requirements Document (BRD)

**Project:** NFA — Note for Approval Workflow Management System  
**Document Type:** Business Requirements Document  
**Version:** 1.0  
**Status:** Draft for Review

---

# 1. Purpose

The NFA (Note for Approval) Workflow Management System is an internal company application used to create, process, approve, reject, return and track NFA requests.

The system will provide a controlled workflow between Buyers/Initiators and Approvers while allowing Administrators to configure department-wise approver selection and Return behavior.

The system will also maintain complete request, attachment and workflow history for auditability.

---

# 2. Objectives

The primary objectives are:

- Digitize the NFA approval process.
- Replace manual approval tracking with a centralized workflow.
- Allow Buyers to create and submit NFA requests.
- Allow up to 8 approvers to be associated with an NFA.
- Support sequential approval.
- Allow Approvers to Accept, Reject or Return an NFA.
- Allow Admin to configure department-wise approver selection.
- Support both Manual and Dynamic Approver selection.
- Allow Admin to configure Return behavior.
- Maintain complete NFA workflow history.
- Maintain attachment history when documents are changed.
- Support request revisions after Return.
- Provide role-based access.
- Provide Local and AD authentication modes.
- Allow Auditors to view approved NFAs by Department.

---

# 3. User Roles

The system will initially support four roles:

1. Buyer
2. Admin
3. Approver
4. Auditor

A System User can have multiple roles.

For example:

A user can simultaneously be:

- Buyer
- Approver

or:

- Admin
- Buyer
- Auditor

Roles must therefore be maintained independently from the User record.

---

# 4. Employee Master

Employee Master represents the company's employee data used by the NFA application.

Initially, Employee Master data will be maintained manually within the system/database.

The Employee Master will contain employees who may or may not be System Users.

Employee Master is the source used when an employee needs to be searched or selected as an Approver.

There are no restrictions on which employee can be selected from Employee Master as a Dynamic Approver.

---

# 5. System User

System User represents employees who participate in the NFA application.

A System User will be linked to an Employee Master record.

An employee can exist in Employee Master without being a System User.

The system must prevent duplicate System Users for the same Employee Master employee.

---

# 6. Approver User Mapping

When an employee is selected as an Approver:

### If the employee is not a System User

The system will:

1. Identify the employee from Employee Master.
2. Create the corresponding System User.
3. Assign the Approver role.

### If the employee already exists as a System User

The existing System User will be retained.

If the user does not already have the Approver role:

- Add the Approver role.

Existing roles must not be removed.

Example:

Before:

Buyer

After being selected as Approver:

Buyer + Approver

No duplicate User record will be created.

---

# 7. Authentication

The application will support two authentication modes:

## 7.1 LOCAL Authentication

When Local authentication is selected:

1. User enters their login credentials.
2. The system checks the password against the local database.
3. If credentials are valid, the user is authenticated.
4. The user is redirected to the Dashboard.
5. If credentials are invalid, the user remains on the Login page and receives an appropriate error message.

---

## 7.2 AD Authentication

When AD authentication is selected:

1. User enters:
   - User Alias
   - Password
2. The application sends the User Alias and Password to the configured AD authentication URL.
3. The response from the AD endpoint will contain an `isSuccess` result.
4. If `isSuccess = true`:
   - Authenticate the user.
   - Redirect the user to Dashboard.
5. If `isSuccess = false`:
   - Do not authenticate the user.
   - Keep the user on the Login page.
   - Display an appropriate authentication failure message.

The actual AD URL will be provided/configured separately.

The AD authentication endpoint must not be hard-coded into the application.

---

# 8. Role-Based Access

After successful authentication, the system will identify the System User and associated roles.

The available application functionality will be based on the user's roles.

A user with multiple roles must be able to access the functionality associated with each assigned role, subject to authorization rules.

Backend authorization must also be enforced.

---

# 9. Department

Departments will be maintained within the NFA system.

Department selection is relevant to:

- NFA creation
- Department-wise approver configuration
- Auditor filtering

---

# 10. Department-Wise Approver Configuration

The Admin will configure the Approver selection mode for each Department.

There are two modes:

## 10.1 Manual Approver

Admin can manually configure multiple Approvers for a Department.

The system must support multiple configured Approvers.

The exact configured approval sequence will be associated with the Department configuration/NFA workflow as applicable.

---

## 10.2 Dynamic Approver

When Dynamic mode is configured:

The Buyer will search the Employee Master and directly select the required Approver.

There are no restrictions on which Employee Master employee can be selected.

Dynamic Approver does NOT mean:

- Department Head
- Reporting Manager
- Designation-based selection
- Hierarchy-based selection
- Automatic manager selection
- Any other automatic employee-selection rule

It simply means:

**Employee Master → Search → Select Employee → Map/ensure System User as Approver.**

---

# 11. NFA Request

A Buyer/Initiator will create an NFA Request.

The request will contain:

- Subject / Title
- Department
- Estimated Cost
- Business Justification
- Commercial Impact

These fields will be captured during NFA creation.

Required-field validation will be applied to mandatory fields.

---

# 12. NFA Creation Process

The NFA creation process will consist of the following stages:

### Step 1 — Request Details

Buyer enters:

- Subject / Title
- Department
- Estimated Cost
- Business Justification
- Commercial Impact

### Step 2 — Attachments

Buyer uploads supporting documents.

### Step 3 — Approvers

The system determines whether the Department uses:

- Manual Approver
- Dynamic Approver

The applicable approver process is followed.

A maximum of **8 Approvers** can be associated with an NFA.

### Step 4 — Review

The Buyer reviews the complete NFA.

The review should display:

- Request details
- Department
- Cost
- Business justification
- Commercial impact
- Attachments
- Approver sequence

### Step 5 — Submit

The Buyer confirms submission.

The NFA then enters the approval workflow.

---

# 13. Draft NFA

The Buyer must be able to save an incomplete NFA as a Draft.

A Draft:

- Has not entered the approval workflow.
- Can be opened later by the Buyer.
- Can be completed.
- Can have details/attachments/approvers added before submission.

The Draft can eventually be submitted once all required information is complete.

---

# 14. Approver Sequence

An NFA can have a maximum of 8 Approvers.

Approvers are maintained in sequence.

Example:

1. Approver A
2. Approver B
3. Approver C
4. Approver D

After submission, the NFA moves sequentially through the approval list.

---

# 15. Approver List After Submission

Once an NFA has been submitted:

**The Buyer cannot change the Approver list.**

The Approver sequence associated with the submitted NFA remains fixed.

This restriction also applies when the NFA is returned.

The Buyer may modify the NFA information after Return, but cannot modify the Approver list.

---

# 16. Approver Actions

The Approver will have three primary actions:

## Accept

The Approver accepts the NFA.

The system moves the NFA to the next Approver.

If there is no next Approver, the NFA becomes Approved.

---

## Reject

The Approver rejects the NFA.

The NFA workflow stops.

Rejected is a final state.

An Admin cannot reopen a rejected NFA.

---

## Return

The Approver returns the NFA.

The NFA follows the Return Mode configured by Admin.

---

# 17. Return Configuration

Return behavior is completely separate from Department Approver configuration.

The Admin will configure one of two Return Modes:

### Option 1 — Return to Initiator

The NFA is sent to the original Buyer/Initiator.

After the Buyer modifies and resubmits the NFA, the workflow resumes from the Approver who returned the NFA.

Example:

Buyer  
→ Approver 1  
→ Approver 2  
→ Return  
→ Buyer  
→ Resubmit  
→ Approver 2  
→ Approver 3

---

### Option 2 — Return to Previous Approver

The NFA is sent to the immediately previous Approver according to the configured workflow.

The complete action must be recorded in the NFA history.

---

# 18. Returned NFA Editing

When an NFA is returned to the Buyer/Initiator:

The Buyer can modify the overall NFA information.

This includes the request information and applicable attachments.

However:

**The Approver list cannot be changed after submission.**

After making the required changes, the Buyer can resubmit the NFA.

---

# 19. Request Revision

When a returned NFA is modified, the system must preserve the previous version.

Example:

### Version 1

Original NFA submitted.

↓

Approver returns NFA.

↓

### Version 2

Buyer modifies the NFA.

↓

Buyer resubmits.

The system must retain the ability to identify previous and current request information.

---

# 20. Attachments

Attachments are associated with the NFA.

When an attachment is changed after Return, the previous attachment must not simply be deleted/overwritten.

A new attachment version should be created.

Example:

Version 1:

`quotation.pdf`

After Return:

Version 2:

`revised_quotation.pdf`

Both versions must remain traceable.

---

# 21. Workflow History

The system must maintain complete history against every NFA Request ID.

History must include important actions such as:

- Draft created
- Submitted
- Accepted
- Rejected
- Returned
- Resubmitted

The history should capture appropriate information including:

- Request ID
- User
- Employee
- Approver sequence
- Action
- Previous status
- New status
- Comments/reason
- Date/time
- Workflow cycle/revision

Historical records must not be overwritten.

---

# 22. Current Status

The NFA Request must maintain its current status separately from its history.

Possible statuses include:

- Draft
- Submitted
- Pending Approval
- Returned
- Rejected
- Approved

The current status represents the current state.

The History represents the complete journey.

---

# 23. Example of Return and History

Example:

### First Workflow Cycle

Buyer submits.

```text
Buyer → Submitted
Approver 1 → Accepted
Approver 2 → Accepted
Approver 3 → Returned
```

The history retains all four actions.

The Buyer modifies the request.

A new request revision is created.

Buyer resubmits.

### Second Workflow Cycle

```text
Buyer → Resubmitted
Approver 3 → Accepted
Approver 4 → Accepted
```

The original history remains unchanged.

The complete NFA journey can therefore be reconstructed.

---

# 24. Auditor

The Auditor role has a specific viewing purpose.

Auditors will be able to view **Approved NFAs only**.

The Auditor will select a Department using a Department dropdown.

The system will display Approved NFAs associated with the selected Department, subject to the applicable access rules.

Auditors will not be provided with Buyer/Approver workflow actions unless separately defined in future requirements.

---

# 25. Notifications

The system will support notifications.

Notifications are required for workflow events such as applicable:

- New approval assignment
- NFA Return
- NFA Rejection
- NFA Approval
- Resubmission
- Other relevant workflow events

The exact notification channels and templates can be defined during technical/design implementation.

The system should be designed to support:

- In-app notifications
- Email notifications

---

# 26. Admin Responsibilities

Admin functionality will include configuration/management of:

- System Users
- Roles
- Departments
- Department-wise Approver Mode
- Manual Approvers
- Return Mode

Admin configuration must not modify historical NFA workflow records that have already been processed.

Existing NFA records should retain their own approval information/history.

---

# 27. NFA Workflow — Overall

The overall process is:

```text
Login
  ↓
Dashboard
  ↓
Buyer
  ↓
Create NFA
  ↓
Request Details
  ↓
Attachments
  ↓
Approvers
  ↓
Review
  ↓
Submit
  ↓
Approver 1
  ↓
Accept / Reject / Return
```

If Accept:

```text
Next Approver
```

If Reject:

```text
Rejected
END
```

If Return:

```text
Configured Return Destination
        ↓
Modify
        ↓
Resubmit
        ↓
Resume Workflow
```

If the NFA reaches the final Approver and is accepted:

```text
Approved
```

---

# 28. Authentication Flow

## Local

```text
Login
 ↓
Local Database
 ↓
Validate Credentials
 ↓
Success → Dashboard
Failure → Login Page
```

## AD

```text
Login
 ↓
User Alias + Password
 ↓
Configured AD URL
 ↓
AD Response
 ↓
isSuccess?
 ├── true → Dashboard
 └── false → Login Page
```

---

# 29. Important Business Rules

The following rules are confirmed:

1. Employee Master is the source for employee selection.
2. Employee Master data will initially be maintained manually.
3. System User represents NFA system participants.
4. A User can have multiple roles.
5. Dynamic Approver means direct search/selection from Employee Master.
6. There are no restrictions on Dynamic Approver employee selection.
7. If selected employee is not a User, create the User.
8. If selected employee already exists as a User, do not create another User.
9. If existing User does not have Approver role, add the Approver role.
10. Existing roles must not be removed.
11. Department Approver Mode can be Manual or Dynamic.
12. Manual configuration supports multiple Approvers.
13. Maximum 8 Approvers per NFA.
14. Approver list cannot be changed after submission.
15. Buyer can save NFA as Draft.
16. Buyer can modify the overall NFA after Return.
17. Rejected NFAs are final.
18. Admin cannot reopen a rejected NFA.
19. Return Mode is independently configurable.
20. Return can go to Initiator or Previous Approver.
21. Returned NFA retains its history.
22. Request revisions must be preserved.
23. Attachment revisions must be preserved.
24. Auditor can view Approved NFAs based on Department selection.
25. Notifications are required.
26. Authentication supports Local and AD modes.

---

# 30. Requirements Not Yet Defined

The following items have intentionally NOT been assumed and should be finalized later:

- Exact Employee Master fields
- Exact AD API request/response structure
- Exact Local password policy
- Exact notification templates
- Exact notification timing
- Exact fields that must be mandatory beyond the stated requirements
- Exact Manual Approver administration UI
- Exact behavior of Return to Previous Approver after the previous approver receives it
- Exact Auditor filtering/access boundaries beyond Department and Approved status
- Exact file types and maximum attachment sizes
- Exact deployment environment
- Exact password reset process
- Exact session timeout policy

These should be treated as open requirements and must not be invented during development.

---

# 31. Success Criteria

The NFA system will be considered functionally successful when:

- Users can authenticate through Local or AD mode.
- Users are identified as System Users.
- Multiple roles can be assigned to users.
- Buyers can create and save Draft NFAs.
- Buyers can submit complete NFAs.
- Departments can be configured for Manual or Dynamic Approver selection.
- Dynamic Approvers can be selected directly from Employee Master.
- Selected employees are correctly mapped to System User and Approver role.
- Up to 8 Approvers can be assigned.
- Approvers can Accept, Reject or Return.
- Return behavior follows Admin configuration.
- Rejected requests cannot be reopened.
- Returned requests can be modified and resubmitted.
- Approver lists cannot be changed after submission.
- Request and attachment revisions are retained.
- Complete workflow history is retained.
- Notifications are generated for applicable workflow events.
- Auditors can view Approved NFAs by Department.
- Unauthorized users cannot access restricted functionality.

---

# 32. Next Project Phase

This BRD is the business-level source of truth for the NFA application.

The next phase should NOT immediately start coding.

The next phase is:

**Technical Design**

This should define:

1. System architecture
2. Database/ERD
3. Table relationships
4. Workflow state machine
5. Authentication architecture
6. Local authentication flow
7. AD authentication flow
8. Role/permission architecture
9. API structure
10. Attachment/version architecture
11. History architecture
12. Department/Approver configuration architecture

After the Technical Design is finalized, the development-ready Antigravity prompts will be created.

The previously prepared 45-step Foundation Prompt should be treated as a preliminary development prompt and should be updated to align exactly with this approved BRD before being given to Antigravity.
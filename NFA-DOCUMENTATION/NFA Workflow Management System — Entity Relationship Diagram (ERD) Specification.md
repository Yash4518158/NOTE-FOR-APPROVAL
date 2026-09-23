# NFA WORKFLOW MANAGEMENT SYSTEM
## Entity Relationship Diagram (ERD) Specification & Database Schema Design

**Project:** NFA — Note for Approval Workflow Management System  
**Document Type:** ERD Specification & Technical Review  
**Version:** 1.0  
**Status:** Approved Schema Reference  

---

# 1. Executive Review of Provided ERD Diagram (`ERD.png`)

We performed a comprehensive audit comparing the provided diagram (`ERD.png`) against the **Business Requirements Document (BRD)** and **Technical Requirements & Design Document**.

### 🟢 What is Correct & Well-Designed in `ERD.png`:
1. **Strict Employee-to-User Mapping**: 1:1 relationship between `EmployeeMaster` and `SystemUser` with `EmployeeID (Unique)` enforces zero duplicate users per employee.
2. **Flexible Multi-Role Architecture**: Junction table `UserRole` (`SystemUser` ↔ `UserRole` ↔ `Role`) cleanly handles users with multiple roles (e.g. `Buyer` + `Approver`).
3. **Approver Sequence Control**: `NFAApprover` enforces sequential approval levels ($1..8$).
4. **Attachment Version Control**: Two-tier attachment design (`NFAAttachment` + `NFAAttachmentVersion`) preserves old files on Return/Revision.
5. **Immutable History Log**: `NFAApprovalHistory` tracks all workflow actions.

---

### 🟡 Required Enhancements & Corrections:

| Component | Observation in `ERD.png` | Required Correction per BRD & Tech Spec |
| :--- | :--- | :--- |
| **Table Name** | Spelled `NFARequset` (Typo) | Correct spelling to **`NFARequest`**. |
| **Request Fields** | Has `Title` and `Purpose` | Split `Purpose` into explicit **`BusinessJustification`** and **`CommercialImpact`** fields per BRD Section 11. |
| **Return Modes** | `ReturnBehavior (StepBack)` | Expand options to support both **`RETURN_TO_INITIATOR`** and **`RETURN_TO_PREVIOUS_APPROVER`** (StepBack) per BRD Section 17. |
| **Request Revisions** | `NFARequestVersion` only has metadata | Add snapshot fields (`Title`, `EstimatedCost`, `BusinessJustification`, `CommercialImpact`) to record full content per revision. |
| **Audit History** | Missing cycle counter | Add **`WorkflowCycle`** (Int), **`PreviousStatus`**, and **`NewStatus`** to `NFAApprovalHistory` per BRD Section 21 & 23. |

---

# 2. Complete Complete ERD Mermaid Diagram

Below is the complete, corrected Entity Relationship Diagram formatted for GFM / Mermaid rendering:

```mermaid
erDiagram

    EmployeeMaster ||--o| SystemUser : "1:1 Mapping (Unique EmployeeID)"
    Department ||--o{ EmployeeMaster : "belongs to"
    SystemUser ||--o{ UserRole : "has assigned"
    Role ||--o{ UserRole : "belongs to"

    Department ||--o{ DepartmentApproverConfiguration : "configured with"
    DepartmentApproverConfiguration ||--o{ ManualApproverConfiguration : "defines manual approvers (1..8)"
    DepartmentApproverConfiguration ||--o| WorkflowConfiguration : "defines return policy"
    SystemUser ||--o{ ManualApproverConfiguration : "assigned as manual approver"

    SystemUser ||--o{ NFARequest : "initiates"
    Department ||--o{ NFARequest : "belongs to"
    
    NFARequest ||--|{ NFAApprover : "has sequence (1..8)"
    SystemUser ||--o{ NFAApprover : "acts as approver"
    
    NFARequest ||--o{ NFARequestVersion : "has revisions"
    SystemUser ||--o{ NFARequestVersion : "created revision"

    NFARequest ||--o{ NFAAttachment : "has documents"
    NFAAttachment ||--|{ NFAAttachmentVersion : "has file versions"
    SystemUser ||--o{ NFAAttachmentVersion : "uploaded by"

    NFARequest ||--o{ NFAApprovalHistory : "has audit trail"
    SystemUser ||--o{ NFAApprovalHistory : "action performed by"

    EmployeeMaster {
        string EmployeeID PK
        string EmployeeCode UK
        string FirstName
        string LastName
        string Email UK
        string ADUsername UK
        int DepartmentID FK
        boolean IsActive
        datetime CreatedAt
        datetime UpdatedAt
    }

    SystemUser {
        string UserID PK
        string EmployeeID FK, UK
        string Username UK
        string Email UK
        string AuthMode "LOCAL / AD"
        boolean IsActive
        datetime LastLoginAt
        datetime CreatedAt
        datetime UpdatedAt
    }

    Role {
        string RoleID PK
        string RoleCode UK "Buyer / Admin / Approver / Auditor"
        string RoleName
        string Description
        boolean IsActive
    }

    UserRole {
        int UserRoleID PK
        string UserID FK
        string RoleID FK
        datetime AssignedAt
        string AssignedBy FK
    }

    Department {
        int DepartmentID PK
        string DepartmentCode UK
        string DepartmentName
        string Description
        boolean IsActive
    }

    DepartmentApproverConfiguration {
        int ConfigID PK
        int DepartmentID FK
        string ApproverMode "MANUAL / DYNAMIC"
        boolean IsActive
        string CreatedBy FK
        datetime CreatedAt
    }

    ManualApproverConfiguration {
        int ManualConfigID PK
        int ConfigID FK
        int ApproverLevel "1..8"
        string ApproverUserID FK
        boolean IsActive
    }

    WorkflowConfiguration {
        int WorkflowConfigID PK
        int ConfigID FK, UK
        string ReturnMode "RETURN_TO_INITIATOR / RETURN_TO_PREVIOUS_APPROVER"
        datetime UpdatedAt
    }

    NFARequest {
        string NFARequestID PK
        string NFARequestNumber UK "e.g. NFA-2026-00001"
        string InitiatorID FK
        int DepartmentID FK
        string Title
        decimal EstimatedCost
        string Currency
        string BusinessJustification
        string CommercialImpact
        string Status "DRAFT / SUBMITTED / PENDING / RETURNED / REJECTED / APPROVED"
        int CurrentApproverLevel "1..8"
        string CurrentApproverUserID FK
        int CurrentVersionNo
        boolean IsSoftDeleted
        datetime CreatedAt
        datetime UpdatedAt
        datetime SubmittedAt
    }

    NFARequestVersion {
        int NFARequestVersionID PK
        string NFARequestID FK
        int VersionNo
        string VersionType "Original / Revision"
        string Title
        decimal EstimatedCost
        string BusinessJustification
        string CommercialImpact
        string RevisionReason
        string CreatedBy FK
        datetime CreatedAt
    }

    NFAApprover {
        int NFAApproverID PK
        string NFARequestID FK
        int ApproverLevel "1..8"
        string ApproverUserID FK
        string ApprovalStatus "Pending / Approved / Rejected / Returned"
        boolean IsActive
        datetime CreatedAt
    }

    NFAAttachment {
        int AttachmentID PK
        string NFARequestID FK
        string DocumentName
        boolean IsActive
        datetime CreatedAt
    }

    NFAAttachmentVersion {
        int AttachmentVersionID PK
        int AttachmentID FK
        int VersionNo
        string FileName
        string FilePath
        string FileType
        int FileSizeBytes
        string UploadedBy FK
        datetime UploadedAt
    }

    NFAApprovalHistory {
        int ApprovalHistoryID PK
        string NFARequestID FK
        int WorkflowCycle "1, 2, 3..."
        int ApproverLevel "1..8"
        string ActionTaken "SUBMITTED / ACCEPTED / REJECTED / RETURNED / RESUBMITTED"
        string PreviousStatus
        string NewStatus
        string Remarks
        string ActionBy FK
        datetime ActionAt
    }
```

---

# 3. Detailed Data Dictionary & Schema Specification

### 3.1 `EmployeeMaster` (Company Employee Directory)
* **`EmployeeID`** (PK, VARCHAR(50)): Unique Employee Identifier.
* **`EmployeeCode`** (VARCHAR(50), Unique): Company employee code (e.g. `EMP001`).
* **`DepartmentID`** (FK to `Department`): Employee's default department.

### 3.2 `SystemUser` (System Participants)
* **`UserID`** (PK, VARCHAR(50)): System User ID.
* **`EmployeeID`** (FK to `EmployeeMaster`, UNIQUE): Ensures 1:1 mapping with Employee Master.

### 3.3 `UserRole` (Role Assignment Junction)
* **`UserID`** (FK), **`RoleID`** (FK): Multi-role mapping supporting Buyer, Admin, Approver, and Auditor roles simultaneously per user.

### 3.4 `DepartmentApproverConfiguration` & `WorkflowConfiguration`
* **`ApproverMode`**: Enum (`MANUAL`, `DYNAMIC`).
* **`ReturnMode`**: Enum (`RETURN_TO_INITIATOR`, `RETURN_TO_PREVIOUS_APPROVER`).

### 3.5 `NFARequest` & `NFARequestVersion`
* **`NFARequestNumber`**: Human-readable unique string (e.g. `NFA-2026-00001`).
* **`BusinessJustification` & `CommercialImpact`**: Explicit text fields for request justification per BRD Section 11.
* **`NFARequestVersion`**: Snapshots the request content on each Return & Resubmit cycle.

### 3.6 `NFAApprovalHistory` (Append-Only Audit Log)
* **`WorkflowCycle`**: Tracks workflow cycle iterations ($1, 2, 3\dots$) across returns and resubmissions.
* **`ActionTaken`**: (`SUBMITTED`, `ACCEPTED`, `REJECTED`, `RETURNED`, `RESUBMITTED`). Never updated or deleted.

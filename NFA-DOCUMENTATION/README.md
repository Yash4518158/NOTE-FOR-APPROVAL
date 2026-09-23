# Note for Approval (NFA) - Business Requirements & Functional Document

This document outlines the Business Requirements Document (BRD) and Functional Requirements for the Note for Approval (NFA) application, designed to digitize and automate the manual approval process.

## 1. Business Requirements Document (BRD)

### 1.1 Purpose & Objective
The NFA application aims to digitize the process for employees requesting administrative or commercial approvals from their reporting managers, Finance, and Plant Heads. It will replace manual, paper-based, or email-centric processes with a unified, auditable, and tracked digital workflow.

### 1.2 Business Process Overview
1. **Initiation**: Employees log in and create a new NFA request specifying the Department, Subject, Business Justification, and Commercial Impact.
2. **Attachments**: Initiators can attach necessary supporting documents (quotations, specs, etc.).
3. **Sequential Approvals**: Initiator selects up to 8 approvers in a sequential chain (e.g., Reporting Manager → Finance → Plant Head).
4. **Approval Actions**: Each approver is notified sequentially and can Approve, Reject, or Return the request with mandatory comments for rejection/return.
5. **Tracking & Reporting**: The system tracks the status (Draft, Pending, Approved, Rejected, Returned) in real-time. Management can view consolidated reports and aging requests.

### 1.3 Key Stakeholders
- **Initiator**: Creates and submits requests.
- **Approvers (Manager, Finance, Plant Head, etc.)**: Review, approve, reject, or return requests.
- **System/Site Administrator**: Manages master data (Departments, Subjects) and access.
- **Auditor**: Read-only access for compliance.

---

## 2. Functional Requirements Document (FRD)

### 2.1 User Authentication & Access
- Users log in securely (corporate credentials).
- Auto-fill user details (Name, ID, Department, Designation) on the request form.
- Role-based access control (Initiator vs. Approver vs. Admin).

### 2.2 Request Management
- **Creation**: Form to capture Department, Subject, Justification, and Commercial Impact.
- **Auto-generation**: Unique NFA Number (e.g., NFA-PLANT-YYYY-#####).
- **Drafting**: Ability to save requests as drafts before submission.
- **Attachments**: Support for PDF, Word, Excel, JPG/PNG (Max size configured, e.g., 25MB). All attachments retained permanently.

### 2.3 Workflow Engine
- **Sequential Routing**: Requests move to the next approver only after the current one approves.
- **Actions**: Approve, Reject (terminates workflow), Return to Initiator (pauses for correction).
- **Constraints**: Initiators cannot approve their own requests. Max 8 approvers per request.
- **Audit Trail**: Complete, timestamped history of actions and comments.

### 2.4 Notifications & Tracking
- **Email Notifications**: Automated emails on submission, approval routing, rejection, and final approval with direct links to the request.
- **Reminders**: Periodic nudges for pending requests.
- **Visual Tracker**: Step-by-step UI to see where the request is currently blocked.

### 2.5 Reporting & Dashboards
- **My Requests**: View personal submitted requests.
- **Consolidated Reports**: Filterable views of Approved, Rejected, and In-Process requests.
- **Export & Print**: Ability to export reports to Excel/PDF and print individual NFA requests.
- **Ageing View**: Highlight pending requests beyond configured days.

### 2.6 Cross-Platform Accessibility
- The application will be accessible via Desktop, Laptop, Mobile, and iPad. (Responsive UI).

---

## 3. High-Level Future Strategy

We will proceed with separating the architecture into:
- **`NFA-APP`**: For the Frontend logic (UI, forms, dynamic workflow components).
- **`NFA-BACKEND`**: For the Backend API (Business rules, workflow engine, authentication).
- **Separate Database**: We will identify the most suitable Database later (e.g., PostgreSQL, SQL Server, etc.) to store the approval chains and master data.

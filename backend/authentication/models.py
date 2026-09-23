import uuid
from django.db import models

class Department(models.Model):
    department_id = models.AutoField(primary_key=True, db_column='DepartmentID')
    department_name = models.CharField(max_length=100, db_column='DepartmentName')
    department_code = models.CharField(max_length=20, unique=True, db_column='DepartmentCode')
    description = models.CharField(max_length=255, blank=True, null=True, db_column='Description')
    created_at = models.DateTimeField(auto_now_add=True, db_column='CreatedAt')

    class Meta:
        db_table = 'Department'


class Role(models.Model):
    role_id = models.AutoField(primary_key=True, db_column='RoleID')
    role_code = models.CharField(max_length=50, default='', db_column='RoleCode')
    role_name = models.CharField(max_length=100, db_column='RoleName')
    description = models.CharField(max_length=255, blank=True, null=True, db_column='Description')

    class Meta:
        db_table = 'Role'


class EmployeeMaster(models.Model):
    employee_id = models.AutoField(primary_key=True, db_column='EmployeeID')
    employee_code = models.CharField(max_length=50, unique=True, db_column='EmployeeCode')
    first_name = models.CharField(max_length=100, default='', db_column='FirstName')
    last_name = models.CharField(max_length=100, default='', db_column='LastName')
    email = models.EmailField(max_length=150, unique=True, default='user@company.com', db_column='Email')
    department = models.ForeignKey(Department, on_delete=models.CASCADE, db_column='DepartmentID')
    created_at = models.DateTimeField(auto_now_add=True, db_column='CreatedAt')

    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}".strip() or "Employee"

    class Meta:
        db_table = 'EmployeeMaster'


class SystemUser(models.Model):
    user_id = models.AutoField(primary_key=True, db_column='UserID')
    employee = models.OneToOneField(EmployeeMaster, on_delete=models.CASCADE, db_column='EmployeeID')
    username = models.CharField(max_length=100, unique=True, db_column='Username')
    email = models.CharField(max_length=255, null=True, blank=True, db_column='Email')
    password_hash = models.CharField(max_length=255, db_column='PasswordHash')
    created_at = models.DateTimeField(auto_now_add=True, db_column='CreatedAt')

    class Meta:
        db_table = 'SystemUser'


class UserRole(models.Model):
    user_role_id = models.AutoField(primary_key=True, db_column='UserRoleID')
    user = models.ForeignKey(SystemUser, on_delete=models.CASCADE, related_name='user_roles', db_column='UserID')
    role = models.ForeignKey(Role, on_delete=models.CASCADE, db_column='RoleID')

    class Meta:
        db_table = 'UserRole'
        unique_together = ('user', 'role')


class DepartmentApproverConfiguration(models.Model):
    config_id = models.AutoField(primary_key=True, db_column='ConfigID')
    department = models.ForeignKey(Department, on_delete=models.CASCADE, db_column='DepartmentID')
    approver_mode = models.CharField(max_length=20, default='DYNAMIC', db_column='ApproverMode')
    created_at = models.DateTimeField(auto_now_add=True, db_column='CreatedAt')

    class Meta:
        db_table = 'DepartmentApproverConfiguration'


class ManualApproverConfiguration(models.Model):
    manual_config_id = models.AutoField(primary_key=True, db_column='ManualConfigID')
    config = models.ForeignKey(DepartmentApproverConfiguration, on_delete=models.CASCADE, db_column='ConfigID')
    approver_user = models.ForeignKey(SystemUser, on_delete=models.CASCADE, db_column='ApproverUserID')
    approver_level = models.IntegerField(db_column='ApproverLevel')
    is_email_active = models.BooleanField(default=True, db_column='IsEmailActive')
    is_inapp_active = models.BooleanField(default=True, db_column='IsInAppActive')
    created_at = models.DateTimeField(auto_now_add=True, db_column='CreatedAt')
    updated_at = models.DateTimeField(auto_now=True, db_column='UpdatedAt')

    class Meta:
        db_table = 'ManualApproverConfiguration'



class WorkflowConfiguration(models.Model):
    workflow_config_id = models.AutoField(primary_key=True, db_column='WorkflowConfigID')
    return_mode = models.CharField(max_length=255, default='RETURN_TO_INITIATOR', db_column='ReturnMode')
    updated_at = models.DateTimeField(auto_now=True, db_column='UpdatedAt')

    class Meta:
        db_table = 'WorkflowConfiguration'


SystemConfiguration = WorkflowConfiguration


class NFARequest(models.Model):
    nfa_request_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False, db_column='NFARequestID')
    nfa_number = models.CharField(max_length=50, unique=True, db_column='NFANumber')
    buyer = models.ForeignKey(SystemUser, on_delete=models.CASCADE, related_name='created_nfas', db_column='BuyerID')
    department = models.ForeignKey(Department, on_delete=models.CASCADE, db_column='DepartmentID')
    title = models.CharField(max_length=255, db_column='Title')
    total_amount = models.DecimalField(max_digits=18, decimal_places=2, db_column='TotalAmount')
    vendor_name = models.CharField(max_length=150, blank=True, null=True, db_column='VendorName')
    project_name = models.CharField(max_length=150, blank=True, null=True, db_column='ProjectName')
    business_justification = models.TextField(db_column='BusinessJustification')
    commercial_impact = models.TextField(blank=True, null=True, db_column='CommercialImpact')
    current_status = models.CharField(max_length=50, default='DRAFT', db_column='CurrentStatus')
    current_level = models.IntegerField(default=1, db_column='CurrentLevel')
    created_at = models.DateTimeField(auto_now_add=True, db_column='CreatedAt')
    updated_at = models.DateTimeField(auto_now=True, db_column='UpdatedAt')

    class Meta:
        db_table = 'NFARequest'


class NFAApprover(models.Model):
    nfa_approver_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False, db_column='NFAApproverID')
    nfa_request = models.ForeignKey(NFARequest, on_delete=models.CASCADE, related_name='approver_chain', db_column='NFARequestID')
    approver_user = models.ForeignKey(SystemUser, on_delete=models.CASCADE, db_column='ApproverUserID')
    approver_level = models.IntegerField(db_column='ApproverLevel')

    class Meta:
        db_table = 'NFAApprover'


class NFARequestVersion(models.Model):
    nfa_version_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False, db_column='NFAVersionID')
    nfa_request = models.ForeignKey(NFARequest, on_delete=models.CASCADE, related_name='versions', db_column='NFARequestID')
    version_number = models.IntegerField(db_column='VersionNumber')
    snapshot_data = models.JSONField(db_column='SnapshotData')
    created_at = models.DateTimeField(auto_now_add=True, db_column='CreatedAt')

    class Meta:
        db_table = 'NFARequestVersion'


class NFAAttachment(models.Model):
    attachment_id = models.AutoField(primary_key=True, db_column='AttachmentID')
    nfa_request = models.ForeignKey(NFARequest, on_delete=models.CASCADE, related_name='attachments', db_column='NFARequestID')
    nfa_version = models.ForeignKey('NFARequestVersion', on_delete=models.SET_NULL, null=True, blank=True, db_column='NFAVersionID')
    version_number = models.IntegerField(default=1, db_column='VersionNumber')
    file_name = models.CharField(max_length=255, db_column='FileName')
    file_path = models.CharField(max_length=500, db_column='FilePath')
    file_type = models.CharField(max_length=100, db_column='ContentType')
    file_size = models.BigIntegerField(db_column='FileSize')
    is_deleted = models.BooleanField(default=False, db_column='IsDeleted')
    uploaded_at = models.DateTimeField(auto_now_add=True, db_column='UploadedAt')

    class Meta:
        db_table = 'NFAAttachment'


class NFAApprovalHistory(models.Model):
    history_id = models.AutoField(primary_key=True, db_column='HistoryID')
    nfa_request = models.ForeignKey(NFARequest, on_delete=models.CASCADE, related_name='audit_history', db_column='NFARequestID')
    action_by = models.ForeignKey(SystemUser, on_delete=models.CASCADE, db_column='ActionByID')
    action_type = models.CharField(max_length=50, db_column='ActionType')
    comments = models.TextField(blank=True, null=True, db_column='Comments')
    action_at = models.DateTimeField(auto_now_add=True, db_column='ActionAt')

    class Meta:
        db_table = 'NFAApprovalHistory'


class NotificationTemplate(models.Model):
    template_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False, db_column='TemplateID')
    event_type = models.CharField(max_length=50, unique=True, db_column='EventType')
    event_description = models.CharField(max_length=255, db_column='EventDescription')
    email_subject = models.CharField(max_length=255, db_column='EmailSubject')
    html_body = models.TextField(db_column='HtmlBody')
    is_email_active = models.BooleanField(default=True, db_column='IsEmailActive')
    is_inapp_active = models.BooleanField(default=True, db_column='IsInAppActive')
    created_at = models.DateTimeField(auto_now_add=True, db_column='CreatedAt')
    updated_at = models.DateTimeField(auto_now=True, db_column='UpdatedAt')

    class Meta:
        db_table = 'NotificationTemplates'


class InAppNotification(models.Model):
    notification_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False, db_column='NotificationID')
    user = models.ForeignKey(SystemUser, on_delete=models.CASCADE, related_name='notifications', db_column='UserID')
    event_type = models.CharField(max_length=50, db_column='EventType')
    title = models.CharField(max_length=255, db_column='Title')
    message = models.TextField(db_column='Message')
    nfa_request = models.ForeignKey(NFARequest, on_delete=models.SET_NULL, null=True, blank=True, db_column='NFARequestID')
    is_read = models.BooleanField(default=False, db_column='IsRead')
    created_at = models.DateTimeField(auto_now_add=True, db_column='CreatedAt')

    class Meta:
        db_table = 'InAppNotifications'


class SystemErrorLog(models.Model):
    error_id = models.AutoField(primary_key=True, db_column='ErrorID')
    error_source = models.CharField(max_length=100, default='SYSTEM', db_column='ErrorSource')
    exception_type = models.CharField(max_length=150, default='Exception', db_column='ExceptionType')
    error_message = models.TextField(db_column='ErrorMessage')
    stack_trace = models.TextField(blank=True, null=True, db_column='StackTrace')
    user = models.ForeignKey(SystemUser, on_delete=models.SET_NULL, null=True, blank=True, db_column='UserID')
    endpoint = models.CharField(max_length=255, blank=True, null=True, db_column='Endpoint')
    created_at = models.DateTimeField(auto_now_add=True, db_column='CreatedAt')

    class Meta:
        db_table = 'SystemErrorLog'


class StatusMaster(models.Model):
    status_id = models.AutoField(primary_key=True, db_column='StatusID')
    status_code = models.CharField(max_length=50, unique=True, db_column='StatusCode')
    category = models.CharField(max_length=30, default='REQUEST_STATUS', db_column='Category')
    display_label = models.CharField(max_length=100, db_column='DisplayLabel')
    badge_bg_color = models.CharField(max_length=20, default='#eff6ff', db_column='BadgeBgColor')
    badge_text_color = models.CharField(max_length=20, default='#1d4ed8', db_column='BadgeTextColor')
    description = models.TextField(blank=True, null=True, db_column='Description')
    is_active = models.BooleanField(default=True, db_column='IsActive')
    created_at = models.DateTimeField(auto_now_add=True, db_column='CreatedAt')

    class Meta:
        db_table = 'mst_status'


class PolicyDocument(models.Model):
    policy_id = models.AutoField(primary_key=True, db_column='PolicyID')
    title = models.CharField(max_length=255, db_column='Title')
    category = models.CharField(max_length=100, default='PROCUREMENT', db_column='Category')
    version_number = models.IntegerField(default=1, db_column='VersionNumber')
    is_active = models.BooleanField(default=True, db_column='IsActive')
    uploaded_at = models.DateTimeField(auto_now_add=True, db_column='UploadedAt')

    class Meta:
        db_table = 'mst_policy_document'


class PolicyChunk(models.Model):
    chunk_id = models.AutoField(primary_key=True, db_column='ChunkID')
    policy = models.ForeignKey(PolicyDocument, on_delete=models.CASCADE, db_column='PolicyID', related_name='chunks', null=True, blank=True)
    section_title = models.CharField(max_length=255, db_column='SectionTitle')
    chunk_text = models.TextField(db_column='ChunkText')
    keywords = models.CharField(max_length=500, null=True, blank=True, db_column='Keywords')
    min_amount_limit = models.DecimalField(max_digits=18, decimal_places=2, default=0.00, db_column='MinAmountLimit')
    max_amount_limit = models.DecimalField(max_digits=18, decimal_places=2, default=999999999.00, db_column='MaxAmountLimit')
    is_active = models.BooleanField(default=True, db_column='IsActive')
    created_at = models.DateTimeField(auto_now_add=True, db_column='CreatedAt')

    class Meta:
        db_table = 'mst_policy_chunk'


from django.urls import path
from authentication.views import AuthConfigView, LoginView, CurrentUserView, LogoutView
from authentication.admin_views import (
    StatusMasterView,
    AdminReassignmentListView,
    AdminReassignApproverView,
    GlobalConfigView,
    AdminDepartmentConfigListView,
    SetDepartmentApproverModeView,
    SetDepartmentReturnModeView,
    SaveManualApproversView,
    EmployeeSearchView
)
from authentication.nfa_views import (
    SaveNFADraftView, 
    SubmitNFAView, 
    NFARequestListView, 
    NFARequestDetailView, 
    UploadAttachmentView,
    DeleteNFADraftView,
    NFAPendingApprovalsListView,
    EvaluateNFAView,
    ResubmitNFAView
)
from authentication.auditor_views import AuditorNFAListView, NotificationTemplateConfigView, InAppNotificationListView
from authentication.ai.ai_views import AIReviewNFAView, AIApprovalPredictionView

urlpatterns = [
    path('admin/status-master', StatusMasterView.as_view(), name='status_master'),
    path('admin/reassignment-list', AdminReassignmentListView.as_view(), name='admin_reassignment_list'),
    path('admin/reassign-approver', AdminReassignApproverView.as_view(), name='admin_reassign_approver'),
    path('auth/config', AuthConfigView.as_view(), name='auth_config'),
    path('auth/login', LoginView.as_view(), name='login'),
    path('admin/department-config', SetDepartmentApproverModeView.as_view(), name='department_config'),
    path('admin/manual-approvers', SaveManualApproversView.as_view(), name='manual_approvers'),
    path('admin/return-config', SetDepartmentReturnModeView.as_view(), name='return_config'),
    path('admin/global-config', GlobalConfigView.as_view(), name='global_config'),
    path('admin/departments', AdminDepartmentConfigListView.as_view(), name='department_list'),
    path('employees/search', EmployeeSearchView.as_view(), name='employee_search'),
    path('nfa/draft', SaveNFADraftView.as_view(), name='nfa_draft'),
    path('nfa/delete-draft', DeleteNFADraftView.as_view(), name='nfa_delete_draft'),
    path('nfa/submit', SubmitNFAView.as_view(), name='nfa_submit'),
    path('nfa/list', NFARequestListView.as_view(), name='nfa_list'),
    path('nfa/<uuid:pk>', NFARequestDetailView.as_view(), name='nfa_detail'),
    path('nfa/upload-attachment', UploadAttachmentView.as_view(), name='nfa_upload_attachment'),
    path('nfa/pending-approvals', NFAPendingApprovalsListView.as_view(), name='nfa_pending_approvals'),
    path('nfa/evaluate', EvaluateNFAView.as_view(), name='nfa_evaluate'),
    path('nfa/resubmit', ResubmitNFAView.as_view(), name='nfa_resubmit'),
    path('auditor/nfas', AuditorNFAListView.as_view(), name='auditor_nfas'),
    path('admin/notification-templates', NotificationTemplateConfigView.as_view(), name='notification_templates'),
    path('user/notifications', InAppNotificationListView.as_view(), name='user_notifications'),
    path('ai/nfa-review/<str:pk>', AIReviewNFAView.as_view(), name='ai_nfa_review_pk'),
    path('ai/nfa-review', AIReviewNFAView.as_view(), name='ai_nfa_review_draft'),
    path('ai/approval-prediction/<uuid:pk>', AIApprovalPredictionView.as_view(), name='ai_approval_prediction'),
]


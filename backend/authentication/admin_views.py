from authentication.models import StatusMaster
import logging
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.db import transaction, models
from authentication.models import (
    Department, 
    DepartmentApproverConfiguration, 
    ManualApproverConfiguration, 
    WorkflowConfiguration, 
    SystemUser, 
    Role, 
    UserRole, 
    EmployeeMaster, 
    SystemErrorLog,
    NFARequest,
    NFARequestVersion,
    NFAApprovalHistory
)

logger = logging.getLogger(__name__)

class GlobalConfigView(APIView):
    """Gets/Sets global workflow settings (e.g. GLOBAL_RETURN_MODE)"""
    def get(self, request):
        config = WorkflowConfiguration.objects.filter(pk__isnull=False).first()
        val = config.return_mode if config else 'RETURN_TO_INITIATOR'
        return Response({
            'isSuccess': True,
            'global_return_mode': val
        }, status=status.HTTP_200_OK)

    def post(self, request):
        mode = request.data.get('global_return_mode') or request.data.get('return_mode')
        if not mode or mode not in ['RETURN_TO_INITIATOR', 'RETURN_TO_PREVIOUS_APPROVER']:
            return Response({'isSuccess': False, 'message': 'Invalid return_mode'}, status=status.HTTP_400_BAD_REQUEST)

        config = WorkflowConfiguration.objects.first()
        if not config:
            config = WorkflowConfiguration.objects.create(return_mode=mode)
        else:
            config.return_mode = mode
            config.save()

        return Response({
            'isSuccess': True,
            'message': f"Updated Global Return Mode to {mode}",
            'global_return_mode': config.return_mode
        }, status=status.HTTP_200_OK)


class AdminDepartmentConfigListView(APIView):
    """Returns list of all departments with their approver mode and return mode"""
    def get(self, request):
        departments = Department.objects.all().order_by('department_name')
        global_return_config = WorkflowConfiguration.objects.filter(pk__isnull=False).first()
        global_return_mode = global_return_config.return_mode if global_return_config else 'RETURN_TO_INITIATOR'

        result = []
        for dept in departments:
            dept_config = DepartmentApproverConfiguration.objects.filter(department=dept).first()
            approver_mode = dept_config.approver_mode if dept_config else 'DYNAMIC'

            manual_list = []
            if dept_config:
                manual_approvers_qs = ManualApproverConfiguration.objects.filter(config=dept_config).order_by('approver_level')
                for item in manual_approvers_qs:
                    if item.approver_user:
                        manual_list.append({
                            'approver_level': item.approver_level,
                            'user_id': item.approver_user.user_id,
                            'full_name': item.approver_user.employee.full_name if item.approver_user.employee else item.approver_user.username,
                            'employee_code': item.approver_user.employee.employee_code if item.approver_user.employee else item.approver_user.username,
                            'email': item.approver_user.email or (item.approver_user.employee.email if item.approver_user.employee else f"{item.approver_user.username}@company.com"),
                        })


            result.append({
                'department_id': dept.department_id,
                'department_code': dept.department_code,
                'department_name': dept.department_name,
                'approver_mode': approver_mode,
                'return_mode': global_return_mode,
                'manual_approvers': manual_list,
            })

        return Response({'isSuccess': True, 'departments': result}, status=status.HTTP_200_OK)


class SetDepartmentApproverModeView(APIView):
    """Sets Department Approver Mode (MANUAL vs DYNAMIC)"""
    def post(self, request):
        department_id = request.data.get('department_id')
        approver_mode = request.data.get('approver_mode')

        if not department_id or approver_mode not in ['MANUAL', 'DYNAMIC']:
            return Response({'isSuccess': False, 'message': 'Valid department_id and approver_mode required.'}, status=status.HTTP_400_BAD_REQUEST)

        dept = Department.objects.filter(department_id=department_id).first()
        if not dept:
            return Response({'isSuccess': False, 'message': 'Department not found'}, status=status.HTTP_404_NOT_FOUND)

        config, _ = DepartmentApproverConfiguration.objects.get_or_create(department=dept)
        config.approver_mode = approver_mode
        config.save()

        return Response({
            'isSuccess': True,
            'message': f"Updated {dept.department_name} Approver Mode to {approver_mode}",
            'department_id': dept.department_id,
            'approver_mode': config.approver_mode
        }, status=status.HTTP_200_OK)


class SetDepartmentReturnModeView(APIView):
    """Sets Global Return Mode"""
    def post(self, request):
        return_mode = request.data.get('return_mode')
        if not return_mode or return_mode not in ['RETURN_TO_INITIATOR', 'RETURN_TO_PREVIOUS_APPROVER']:
            return Response({'isSuccess': False, 'message': 'Valid return_mode required.'}, status=status.HTTP_400_BAD_REQUEST)

        config = WorkflowConfiguration.objects.first()
        if not config:
            config = WorkflowConfiguration.objects.create(return_mode=return_mode)
        else:
            config.return_mode = return_mode
            config.save()

        return Response({
            'isSuccess': True,
            'message': f"Updated Global Return Mode to {return_mode}",
            'return_mode': config.return_mode
        }, status=status.HTTP_200_OK)


        return Response({
            'isSuccess': True,
            'message': f"Updated Global Return Mode to {return_mode}",
            'return_mode': config.return_mode
        }, status=status.HTTP_200_OK)


class SaveManualApproversView(APIView):
    """Saves and orders Manual Approvers sequence (1..8) for a Department"""
    @transaction.atomic
    def post(self, request):
        department_id = request.data.get('department_id')
        approver_user_ids = request.data.get('approver_user_ids', [])

        if not department_id or not isinstance(approver_user_ids, list):
            return Response({'isSuccess': False, 'message': 'Invalid department_id or approver_user_ids list.'}, status=status.HTTP_400_BAD_REQUEST)

        if len(approver_user_ids) > 8:
            return Response({'isSuccess': False, 'message': 'Maximum 8 approvers allowed per department.'}, status=status.HTTP_400_BAD_REQUEST)

        dept = Department.objects.filter(department_id=department_id).first()
        if not dept:
            return Response({'isSuccess': False, 'message': 'Department not found'}, status=status.HTTP_404_NOT_FOUND)

        config, _ = DepartmentApproverConfiguration.objects.get_or_create(department=dept)
        # Remove old manual approver configuration for department
        ManualApproverConfiguration.objects.filter(config=config).delete()

        approver_role, _ = Role.objects.get_or_create(role_code='Approver', defaults={'role_name': 'Workflow Approver'})

        created_seq = []
        for index, user_id in enumerate(approver_user_ids, start=1):
            user = SystemUser.objects.filter(user_id=user_id).first()
            if user:
                UserRole.objects.get_or_create(user=user, role=approver_role)
                item = ManualApproverConfiguration.objects.create(
                    config=config,
                    approver_user=user,
                    approver_level=index,
                    is_email_active=True,
                    is_inapp_active=True
                )

                created_seq.append({
                    'approver_level': index,
                    'full_name': user.employee.full_name,
                    'employee_code': user.employee.employee_code,
                })

        return Response({
            'isSuccess': True,
            'message': f"Configured {len(created_seq)} manual approvers for {dept.department_name}",
            'department_id': dept.department_id,
            'manual_approvers': created_seq
        }, status=status.HTTP_200_OK)


class EmployeeSearchView(APIView):
    """Searches EmployeeMaster and returns provisioning status"""
    def get(self, request):
        query = request.query_params.get('q', '').strip()
        dept_id = request.query_params.get('department_id')

        qs = EmployeeMaster.objects.all()
        if query:
            qs = qs.filter(
                models.Q(first_name__icontains=query) |
                models.Q(last_name__icontains=query) |
                models.Q(employee_code__icontains=query) |
                models.Q(email__icontains=query)
            )
        if dept_id:
            qs = qs.filter(department_id=dept_id)

        results = []
        for emp in qs[:20]:
            sys_user = SystemUser.objects.filter(employee=emp).first()
            results.append({
                'employee_id': emp.employee_id,
                'employee_code': emp.employee_code,
                'full_name': emp.full_name,
                'first_name': emp.first_name,
                'last_name': emp.last_name,
                'email': emp.email,
                'department_id': emp.department.department_id,
                'department_name': emp.department.department_name,
                'has_system_user': sys_user is not None,
                'user_id': sys_user.user_id if sys_user else None,
                'username': sys_user.username if sys_user else None,
            })

        return Response({'isSuccess': True, 'employees': results}, status=status.HTTP_200_OK)


class SystemErrorLogListView(APIView):
    """Lists system error and stack trace logs for Admin viewing"""
    def get(self, request):
        logs_qs = SystemErrorLog.objects.all().order_by('-created_at')[:50]
        logs = []
        for item in logs_qs:
            logs.append({
                'log_id': str(item.log_id),
                'error_source': item.error_source,
                'exception_type': item.exception_type,
                'error_message': item.error_message,
                'stack_trace': item.stack_trace,
                'username': item.user.username if item.user else 'Anonymous',
                'endpoint': item.endpoint,
                'created_at': item.created_at.isoformat(),
            })

        return Response({'isSuccess': True, 'error_logs': logs}, status=status.HTTP_200_OK)


class TestTriggerErrorView(APIView):
    """Test endpoint to trigger a simulated backend error and verify SystemErrorLog logging"""
    def get(self, request):
        val = 1 / 0
        return Response({'val': val})


class AdminReassignmentListView(APIView):
    """Lists active in-progress NFAs and their approver chains for Admin Reassignment"""
    def get(self, request):
        nfas = NFARequest.objects.filter(current_status='PENDING_APPROVAL').order_by('-created_at')
        result = []
        for nfa in nfas:
            version_obj = NFARequestVersion.objects.filter(nfa_request=nfa).order_by('-version_number').first()
            chain = []
            if version_obj and version_obj.snapshot_data and 'approver_chain' in version_obj.snapshot_data:
                raw_chain = version_obj.snapshot_data['approver_chain']
                for step in raw_chain:
                    lvl = step.get('level', 1)
                    chain.append({
                        'level': lvl,
                        'user_id': step.get('user_id'),
                        'username': step.get('username'),
                        'full_name': step.get('full_name'),
                        'email': step.get('email'),
                        'department_name': step.get('department_name', 'General'),
                        'is_editable': lvl >= nfa.current_level,  # Past completed levels are LOCKED
                        'is_reassigned': step.get('is_reassigned', False),
                        'old_approver_name': step.get('old_approver_name', ''),
                        'reassignment_reason': step.get('reassignment_reason', ''),
                    })
            
            result.append({
                'nfa_request_id': str(nfa.nfa_request_id),
                'nfa_number': nfa.nfa_number,
                'title': nfa.title,
                'department_name': nfa.department.department_name if nfa.department else 'General',
                'total_amount_usd': str(nfa.total_amount),
                'current_level': nfa.current_level,
                'current_status': nfa.current_status,
                'buyer_name': nfa.buyer.employee.full_name if nfa.buyer and hasattr(nfa.buyer, 'employee') else 'N/A',
                'buyer_email': nfa.buyer.employee.email if nfa.buyer and hasattr(nfa.buyer, 'employee') else '',
                'approver_chain': chain,
                'version_number': version_obj.version_number if version_obj else 1,
            })

        return Response({'isSuccess': True, 'nfas': result}, status=status.HTTP_200_OK)


class AdminReassignApproverView(APIView):
    """Reassigns an approver in an active NFA approval chain, writing audit log and notifying stakeholders"""
    def post(self, request):
        from authentication.notification_engine import NotificationEngine
        from authentication.models import NFARequest, NFARequestVersion, NFAApprovalHistory, SystemUser, SystemErrorLog
        from django.utils import timezone

        nfa_id = request.data.get('nfa_request_id')
        target_level = request.data.get('level')
        new_user_id = request.data.get('new_user_id')
        admin_id = request.data.get('admin_id') or 1
        reason = request.data.get('reason') or 'Employee Resignation'

        if not nfa_id or not target_level or not new_user_id:
            return Response({'isSuccess': False, 'message': 'nfa_request_id, level, and new_user_id are required.'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            target_level = int(target_level)
            new_user_id = int(new_user_id)
        except ValueError:
            return Response({'isSuccess': False, 'message': 'level and new_user_id must be integers.'}, status=status.HTTP_400_BAD_REQUEST)

        nfa = NFARequest.objects.filter(nfa_request_id=nfa_id).first()
        if not nfa:
            return Response({'isSuccess': False, 'message': 'NFA Request not found.'}, status=status.HTTP_404_NOT_FOUND)

        if nfa.current_status != 'PENDING_APPROVAL':
            return Response({'isSuccess': False, 'message': 'Can only reassign approvers for active in-progress NFAs.'}, status=status.HTTP_400_BAD_REQUEST)

        # 1. Enforce In-Flight Level Scoping (Block past completed levels)
        if target_level < nfa.current_level:
            return Response({
                'isSuccess': False,
                'message': f'Cannot replace approver for Level {target_level} as it has already completed evaluation. Current active level is Level {nfa.current_level}.'
            }, status=status.HTTP_400_BAD_REQUEST)

        new_user = SystemUser.objects.filter(user_id=new_user_id).first()
        if not new_user or not hasattr(new_user, 'employee'):
            return Response({'isSuccess': False, 'message': 'Replacement employee user not found.'}, status=status.HTTP_404_NOT_FOUND)

        admin_user = SystemUser.objects.filter(user_id=admin_id).first() or nfa.buyer

        # 2. Update snapshot data in latest version
        version_obj = NFARequestVersion.objects.filter(nfa_request=nfa).order_by('-version_number').first()
        if not version_obj or not version_obj.snapshot_data or 'approver_chain' not in version_obj.snapshot_data:
            return Response({'isSuccess': False, 'message': 'NFA Version snapshot data missing.'}, status=status.HTTP_400_BAD_REQUEST)

        snapshot_data = dict(version_obj.snapshot_data)
        chain = list(snapshot_data.get('approver_chain', []))
        
        target_step = None
        for step in chain:
            if int(step.get('level', 0)) == target_level:
                target_step = step
                break

        if not target_step:
            return Response({'isSuccess': False, 'message': f'Level {target_level} not found in NFA approver chain.'}, status=status.HTTP_400_BAD_REQUEST)

        old_user_id = target_step.get('user_id')
        old_user_name = target_step.get('full_name', f'User #{old_user_id}')
        old_user = SystemUser.objects.filter(user_id=old_user_id).first()

        # Update step details
        target_step['user_id'] = new_user.user_id
        target_step['username'] = new_user.username
        target_step['full_name'] = new_user.employee.full_name
        target_step['email'] = new_user.employee.email
        target_step['department_name'] = new_user.employee.department.department_name if new_user.employee.department else 'General'
        target_step['is_reassigned'] = True
        target_step['old_approver_name'] = old_user_name
        target_step['reassignment_reason'] = reason
        target_step['reassigned_at'] = timezone.now().isoformat()

        snapshot_data['approver_chain'] = chain
        version_obj.snapshot_data = snapshot_data
        version_obj.save()

        # 3. Write Audit History Record
        history_comment = f"Admin reassigned Level {target_level} Approver from {old_user_name} to {new_user.employee.full_name}. Reason: {reason}"
        NFAApprovalHistory.objects.create(
            nfa_request=nfa,
            action_by=admin_user,
            action_type='APPROVER_REASSIGNED',
            comments=history_comment
        )

        # 4. Multi-Party Notification Triggers (Buyer, Old Approver, New Approver, Chain Members)
        ctx = {
            'nfa_request_id': str(nfa.nfa_request_id),
            'nfa_number': nfa.nfa_number,
            'title': nfa.title,
            'level': target_level,
            'current_level': nfa.current_level,
            'old_approver_name': old_user_name,
            'new_approver_name': new_user.employee.full_name,
            'approver_name': new_user.employee.full_name,
            'buyer_name': nfa.buyer.employee.full_name if nfa.buyer and hasattr(nfa.buyer, 'employee') else 'Buyer',
            'reason': reason,
            'total_amount_usd': str(nfa.total_amount)
        }

        # A. Notify New Approver
        NotificationEngine.trigger_event('EVENT_APPROVER_ASSIGNED', new_user, ctx)

        # B. Notify Buyer
        if nfa.buyer:
            NotificationEngine.trigger_event('EVENT_APPROVER_REASSIGNED', nfa.buyer, ctx)

        # C. Notify Old Replaced Approver (if exists)
        if old_user:
            NotificationEngine.trigger_event('EVENT_APPROVER_REASSIGNED', old_user, ctx)

        return Response({
            'isSuccess': True,
            'message': f"Level {target_level} Approver successfully updated to {new_user.employee.full_name}.",
            'nfa_number': nfa.nfa_number,
            'level': target_level,
            'old_approver_name': old_user_name,
            'new_approver_name': new_user.employee.full_name
        }, status=status.HTTP_200_OK)


class StatusMasterView(APIView):
    def get(self, request):
        statuses = StatusMaster.objects.filter(is_active=True).order_by('status_id')
        results = []
        for s in statuses:
            results.append({
                'status_id': s.status_id,
                'status_code': s.status_code,
                'category': s.category,
                'display_label': s.display_label,
                'badge_bg_color': s.badge_bg_color,
                'badge_text_color': s.badge_text_color,
                'description': s.description
            })
        return Response({'isSuccess': True, 'statuses': results})

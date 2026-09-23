from django.db.models import Count, Q
import os
import uuid
from decimal import Decimal
from django.conf import settings
from django.db import models, transaction
from django.utils import timezone
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.parsers import MultiPartParser, FormParser
from authentication.notification_engine import NotificationEngine
from authentication.ai.services.approval_predictor import ApprovalPredictor
from .models import (

    NFARequest, NFAApprover, NFARequestVersion, NFAAttachment, NFAApprovalHistory, WorkflowConfiguration,
    Department, SystemUser, SystemConfiguration, ManualApproverConfiguration, DepartmentApproverConfiguration
)


def generate_nfa_number() -> str:
    """Generates unique reference number e.g. NFA-2026-08-0001"""
    now = timezone.now()
    year_month = now.strftime("%Y-%m")
    count = NFARequest.objects.count() + 1
    return f"NFA-{year_month}-{count:04d}"


class SaveNFADraftView(APIView):
    """Creates or updates an NFA in DRAFT state"""
    @transaction.atomic
    def post(self, request):
        nfa_id = request.data.get('nfa_request_id')
        buyer_id = request.data.get('buyer_id', 1)  # Default to admin/buyer user

        buyer = SystemUser.objects.filter(user_id=buyer_id).first()
        if not buyer:
            return Response({'isSuccess': False, 'message': 'Buyer user not found.'}, status=status.HTTP_400_BAD_REQUEST)

        dept_id = request.data.get('department_id')
        dept = Department.objects.filter(department_id=dept_id).first() if dept_id else buyer.employee.department

        title = request.data.get('title', 'Untitled NFA Draft').strip()
        project_name = request.data.get('project_name', '').strip()
        business_justification = request.data.get('business_justification', '').strip()
        commercial_impact = request.data.get('commercial_impact', '').strip()
        total_amount = Decimal(str(request.data.get('total_amount', 0.00)))
        vendor_name = request.data.get('vendor_name', '').strip()

        if nfa_id:
            nfa = NFARequest.objects.filter(nfa_request_id=nfa_id, buyer=buyer).first()
            if not nfa:
                return Response({'isSuccess': False, 'message': 'NFA Request not found or permission denied.'}, status=status.HTTP_404_NOT_FOUND)
            if nfa.current_status not in ['DRAFT', 'RETURNED']:
                return Response({'isSuccess': False, 'message': 'Submitted NFAs are locked and cannot be edited as draft.'}, status=status.HTTP_400_BAD_REQUEST)
            
            nfa.title = title
            nfa.department = dept
            nfa.project_name = project_name
            nfa.business_justification = business_justification
            nfa.commercial_impact = commercial_impact
            nfa.total_amount = total_amount
            nfa.vendor_name = vendor_name
            nfa.save()
        else:
            nfa_number = generate_nfa_number()
            nfa = NFARequest.objects.create(
                nfa_number=nfa_number,
                title=title,
                department=dept,
                project_name=project_name,
                business_justification=business_justification,
                commercial_impact=commercial_impact,
                total_amount=total_amount,
                vendor_name=vendor_name,
                current_status='DRAFT',
                current_level=0,
                buyer=buyer
            )
            # Log draft creation in history
            NFAApprovalHistory.objects.create(
                nfa_request=nfa,
                action_by=buyer,
                action_type='CREATED_DRAFT',
                comments='NFA Draft Created'
            )

        # Save selected draft approvers into version snapshot
        approver_user_ids = request.data.get('approver_user_ids', [])
        approver_chain = []
        if isinstance(approver_user_ids, list) and len(approver_user_ids) > 0:
            for idx, u_id in enumerate(approver_user_ids, start=1):
                app_user = SystemUser.objects.filter(user_id=u_id).first()
                if app_user:
                    approver_chain.append({
                        'level': idx,
                        'user_id': app_user.user_id,
                        'username': app_user.username,
                        'full_name': app_user.employee.full_name if hasattr(app_user, 'employee') else app_user.username,
                        'email': (app_user.email or app_user.employee.email) if hasattr(app_user, 'employee') else '',
                        'department_name': app_user.employee.department.department_name if hasattr(app_user, 'employee') and app_user.employee.department else '',
                    })

        # Create or update Draft Version snapshot
        draft_ver, _ = NFARequestVersion.objects.get_or_create(
            nfa_request=nfa,
            version_number=0,
            defaults={'snapshot_data': {}}
        )
        draft_ver.snapshot_data = {
            'title': nfa.title,
            'department_id': nfa.department.department_id if nfa.department else None,
            'project_name': nfa.project_name,
            'business_justification': nfa.business_justification,
            'commercial_impact': nfa.commercial_impact,
            'total_amount_usd': str(nfa.total_amount),
            'vendor_name': nfa.vendor_name,
            'approver_chain': approver_chain,
        }
        draft_ver.save()

        return Response({
            'isSuccess': True,
            'message': f"Draft NFA {nfa.nfa_number} saved successfully.",
            'nfa_request_id': str(nfa.nfa_request_id),
            'nfa_number': nfa.nfa_number,
            'current_status': nfa.current_status,
            'total_amount_usd': str(nfa.total_amount)
        }, status=status.HTTP_200_OK)


class SubmitNFAView(APIView):
    """Submits NFA (DRAFT -> PENDING_APPROVAL), locks fields, creates Version 1 snapshot & history log"""
    @transaction.atomic
    def post(self, request):
        nfa_id = request.data.get('nfa_request_id')
        buyer_id = request.data.get('buyer_id', 1)
        approver_user_ids = request.data.get('approver_user_ids', [])  # Selected approver IDs for DYNAMIC mode

        nfa = NFARequest.objects.filter(nfa_request_id=nfa_id).first()
        if not nfa:
            return Response({'isSuccess': False, 'message': 'NFA Request not found.'}, status=status.HTTP_404_NOT_FOUND)

        if nfa.current_status not in ['DRAFT', 'RETURNED']:
            return Response({'isSuccess': False, 'message': 'This NFA has already been submitted and is currently locked.'}, status=status.HTTP_400_BAD_REQUEST)

        # Validate required form fields for submission
        if not nfa.title or not nfa.business_justification or nfa.total_amount <= 0:
            return Response({'isSuccess': False, 'message': 'Please provide Title, Business Justification, and Amount (₹ INR) before submitting.'}, status=status.HTTP_400_BAD_REQUEST)

        buyer = SystemUser.objects.filter(user_id=buyer_id).first() or nfa.buyer

        # Check Global System Approver Mode from DB table
        dept_config = DepartmentApproverConfiguration.objects.filter(department=nfa.department).first()
        approver_mode = dept_config.approver_mode if dept_config else 'DYNAMIC'

        approver_chain = []
        if approver_mode == 'MANUAL':
            # Auto-populate department pre-configured manual sequence
            dept_config = DepartmentApproverConfiguration.objects.filter(department=nfa.department).first()
            if dept_config:
                manual_qs = ManualApproverConfiguration.objects.filter(config=dept_config, is_active=True).order_by('approver_level')
                for item in manual_qs:
                    approver_chain.append({
                        'level': item.approver_level,
                        'user_id': item.approver_user.user_id,
                        'username': item.approver_user.username,
                        'full_name': item.approver_user.employee.full_name,
                        'email': (item.approver_user.email or item.approver_user.employee.email),
                    })

        if not approver_chain and isinstance(approver_user_ids, list) and len(approver_user_ids) > 0:
            # Dynamic mode or manual fallback: use provided user IDs
            for idx, u_id in enumerate(approver_user_ids, start=1):
                app_user = SystemUser.objects.filter(user_id=u_id).first()
                if app_user:
                    approver_chain.append({
                        'level': idx,
                        'user_id': app_user.user_id,
                        'username': app_user.username,
                        'full_name': app_user.employee.full_name,
                        'email': (app_user.email or app_user.employee.email),
                    })

        if len(approver_chain) == 0:
            # Emergency default: assign approver1
            default_app = SystemUser.objects.filter(username__iexact='approver1').first()
            if default_app:
                approver_chain.append({
                    'level': 1,
                    'user_id': default_app.user_id,
                    'username': default_app.username,
                    'full_name': default_app.employee.full_name,
                    'email': (default_app.email or default_app.employee.email),
                })

        # Create Version 1 Immutable Snapshot
        version_1 = NFARequestVersion.objects.create(
            nfa_request=nfa,
            version_number=1,
            snapshot_data={
                'nfa_number': nfa.nfa_number,
                'title': nfa.title,
                'department_name': nfa.department.department_name,
                'project_name': nfa.project_name,
                'business_justification': nfa.business_justification,
                'commercial_impact': nfa.commercial_impact,
                'total_amount_usd': str(nfa.total_amount),
                'vendor_name': nfa.vendor_name,
                'buyer_username': buyer.username,
                'buyer_full_name': buyer.employee.full_name,
                'approver_chain': approver_chain,
            }
        )

        # Link any existing draft attachments to Version 1 snapshot
        NFAAttachment.objects.filter(nfa_request=nfa, version_number=1).update(
            nfa_version=version_1
        )

        # Transition State: DRAFT -> PENDING_APPROVAL, CurrentLevel = 1
        nfa.current_status = 'PENDING_APPROVAL'
        nfa.current_level = 1
        nfa.save(update_fields=['current_status', 'current_level', 'updated_at'])

        # Write Audit Log
        NFAApprovalHistory.objects.create(
            nfa_request=nfa,
            action_by=buyer,
            action_type='SUBMITTED',
            comments=f"NFA Submitted for Approval (Version 1). Assigned to Level 1 Approver: {approver_chain[0]['full_name']}"
        )

        # Trigger Notifications for Submit Action
        try:
            buyer_user = SystemUser.objects.filter(user_id=buyer_id).first() or nfa.buyer
            buyer_name_str = buyer_user.username if buyer_user else 'Buyer'
            ctx = {
                'nfa_request_id': str(nfa.nfa_request_id),
                'nfa_number': nfa.nfa_number,
                'title': nfa.title,
                'buyer_name': buyer_name_str,
                'total_amount': str(nfa.total_amount),
                'total_amount_usd': str(nfa.total_amount),
                'level': 1
            }
            if buyer_user:
                NotificationEngine.trigger_event('EVENT_NFA_SUBMITTED', buyer_user, ctx)

            # Notify Level 1 Approver
            level1_step = next((s for s in approver_chain if s.get('level') == 1), None)
            if level1_step and level1_step.get('user_id'):
                l1_user = SystemUser.objects.filter(user_id=level1_step['user_id']).first()
                if l1_user:
                    NotificationEngine.trigger_event('EVENT_APPROVER_ASSIGNED', l1_user, ctx)
        except Exception as notif_err:
            pass

        return Response({
            'isSuccess': True,
            'message': f"NFA {nfa.nfa_number} submitted successfully and assigned to {approver_chain[0]['full_name']}.",
            'nfa_request_id': str(nfa.nfa_request_id),
            'nfa_number': nfa.nfa_number,
            'current_status': nfa.current_status,
            'current_level': nfa.current_level,
            'assigned_approver': approver_chain[0]['full_name'],
            'version_number': 1
        }, status=status.HTTP_200_OK)


class NFARequestListView(APIView):
    """Lists NFAs strictly scoped by user role with user-specific decision status"""
    def get(self, request):
        status_filter = request.query_params.get('status', 'ALL').upper()
        role = request.query_params.get('role', 'BUYER').upper()
        user_id = request.query_params.get('user_id') or request.query_params.get('buyer_id')

        user = SystemUser.objects.filter(user_id=user_id).first() if user_id else None

        qs = NFARequest.objects.exclude(current_status__icontains='DELETED').select_related('buyer__employee', 'department').order_by('-created_at')

        # Scope by User Role
        if user:
            if role == 'BUYER':
                qs = qs.filter(buyer=user)
            elif role in ['APPROVER', 'APPROVER_USER']:
                qs = qs.exclude(current_status='DRAFT')
                assigned_ids = set(NFAApprovalHistory.objects.filter(action_by=user).values_list('nfa_request_id', flat=True))
                # Check assigned approvers in latest snapshots in bulk
                latest_vers = NFARequestVersion.objects.order_by('nfa_request_id', '-version_number').distinct('nfa_request_id') if hasattr(NFARequestVersion.objects, 'distinct') else NFARequestVersion.objects.all()
                for v in latest_vers:
                    snap = v.snapshot_data or {}
                    chain = snap.get('approver_chain', [])
                    if any(str(a.get('user_id')) == str(user.user_id) or a.get('username') == user.username for a in chain):
                        assigned_ids.add(v.nfa_request_id)
                qs = qs.filter(nfa_request_id__in=assigned_ids)

        # Bulk fetch user decision history, attachment counts, and version counts to eliminate ALL N+1 queries
        items_batch = list(qs[:100])
        user_decisions_map = {}
        att_counts_map = {}
        ver_counts_map = {}

        if items_batch:
            batch_ids = [item.nfa_request_id for item in items_batch]
            if user:
                user_histories = NFAApprovalHistory.objects.filter(nfa_request_id__in=batch_ids, action_by=user).order_by('action_at')
                for h in user_histories:
                    user_decisions_map[h.nfa_request_id] = h.action_type

            # Bulk attachment counts
            for row in NFAAttachment.objects.filter(nfa_request_id__in=batch_ids, is_deleted=False).values('nfa_request_id').annotate(c=Count('attachment_id')):
                att_counts_map[row['nfa_request_id']] = row['c']

            # Bulk version counts
            for row in NFARequestVersion.objects.filter(nfa_request_id__in=batch_ids).values('nfa_request_id').annotate(c=Count('nfa_version_id')):
                ver_counts_map[row['nfa_request_id']] = row['c']

        results = []
        for item in items_batch:
            my_decision = user_decisions_map.get(item.nfa_request_id, 'PENDING')

            # Filter by status tab if specified
            if status_filter != 'ALL':
                # Normalize status_filter aliases
                target_status = status_filter
                if status_filter in ['PENDING', 'PENDING_APPROVAL']:
                    target_status = 'PENDING_APPROVAL'
                elif status_filter in ['RETURNED', 'REVISE', 'REVISE_RESUBMIT']:
                    target_status = 'RETURNED'

                if role in ['APPROVER', 'APPROVER_USER']:
                    if target_status == 'PENDING_APPROVAL':
                        if item.current_status != 'PENDING_APPROVAL' or my_decision != 'PENDING':
                            continue
                    elif target_status == 'APPROVED':
                        if item.current_status != 'APPROVED' and my_decision != 'APPROVED':
                            continue
                    elif target_status == 'REJECTED':
                        if item.current_status != 'REJECTED' and my_decision != 'REJECTED':
                            continue
                    elif target_status == 'RETURNED':
                        if item.current_status != 'RETURNED' and my_decision != 'RETURNED':
                            continue
                    elif target_status in ['RESUBMITTED', 'REVISED']:
                        v_num = ver_counts_map.get(item.nfa_request_id, 1)
                        if v_num <= 1:
                            continue
                else:
                    if item.current_status != target_status:
                        continue

            pred = ApprovalPredictor.predict_approval_probability(item, attachment_count=att_counts_map.get(item.nfa_request_id, 0), skip_rag=True)

            results.append({
                'nfa_request_id': str(item.nfa_request_id),
                'nfa_number': item.nfa_number,
                'title': item.title,
                'department_name': item.department.department_name if item.department else 'N/A',
                'project_name': item.project_name,
                'total_amount_usd': str(item.total_amount),
                'vendor_name': item.vendor_name,
                'current_status': item.current_status,
                'my_decision': my_decision,
                'current_level': item.current_level,
                'version_number': ver_counts_map.get(item.nfa_request_id, 1),
                'buyer_full_name': item.buyer.employee.full_name if (item.buyer and hasattr(item.buyer, 'employee') and item.buyer.employee) else (item.buyer.username if item.buyer else 'Buyer'),
                'attachment_count': att_counts_map.get(item.nfa_request_id, 0),
                'version_count': ver_counts_map.get(item.nfa_request_id, 1),
                'created_at': item.created_at.isoformat() if item.created_at else None,
                'approval_prediction': pred
            })


        return Response({
            'isSuccess': True,
            'nfa_requests': results,
            'pending_requests': results
        })


class NFARequestDetailView(APIView):
    """Returns complete detail of NFA request, all version snapshots, field diffs, attachments, and history log"""
    def get(self, request, pk):
        nfa = NFARequest.objects.filter(nfa_request_id=pk).first()
        if not nfa:
            return Response({'isSuccess': False, 'message': 'NFA Request not found.'}, status=status.HTTP_404_NOT_FOUND)

        # Get all version snapshots
        versions = nfa.versions.order_by('version_number')
        version_list = []
        for v in versions:
            version_list.append({
                'version_id': str(v.nfa_version_id),
                'version_number': v.version_number,
                'created_at': v.created_at.isoformat(),
                'created_by': nfa.buyer.employee.full_name if nfa.buyer and hasattr(nfa.buyer, 'employee') else 'Buyer',
                'snapshot_data': v.snapshot_data,
            })

        latest_version = versions.last()
        latest_snapshot = latest_version.snapshot_data if latest_version else {}

        # Calculate field diffs between v1 and latest version if v2+ exists
        field_diffs = {}
        if len(version_list) > 1:
            v1_snap = version_list[0]['snapshot_data'] or {}
            v_curr_snap = latest_snapshot or {}

            field_diffs = {
                'title': v1_snap.get('title') != v_curr_snap.get('title'),
                'total_amount_usd': v1_snap.get('total_amount_usd') != v_curr_snap.get('total_amount_usd'),
                'business_justification': v1_snap.get('business_justification') != v_curr_snap.get('business_justification'),
                'commercial_impact': v1_snap.get('commercial_impact') != v_curr_snap.get('commercial_impact'),
                'department_id': v1_snap.get('department_id') != v_curr_snap.get('department_id'),
                'vendor_name': v1_snap.get('vendor_name') != v_curr_snap.get('vendor_name'),
                'project_name': v1_snap.get('project_name') != v_curr_snap.get('project_name'),
                'v1_snapshot': v1_snap,
            }

        # Get attachments (filtering out deleted files and building download URL)
        attachments = []
        for att in nfa.attachments.filter(is_deleted=False):
            file_url = f"http://127.0.0.1:8000/{att.file_path}" if not att.file_path.startswith('http') else att.file_path
            attachments.append({
                'attachment_id': att.attachment_id,
                'file_name': att.file_name,
                'file_path': att.file_path,
                'file_url': file_url,
                'file_size': att.file_size,
                'file_type': att.file_type,
                'version_number': att.nfa_version.version_number if att.nfa_version else 1
            })

        # Get history audit trail (excluding draft logs and simplifying SUBMITTED comments)
        history = []
        for h in nfa.audit_history.all().order_by('action_at'):
            if 'DRAFT' in (h.action_type or '').upper():
                continue

            comment_text = h.comments
            if (h.action_type or '').upper() == 'SUBMITTED':
                comment_text = 'Submitted'

            history.append({
                'history_id': h.history_id,
                'action_by_name': h.action_by.employee.full_name if (h.action_by and hasattr(h.action_by, 'employee') and h.action_by.employee) else (h.action_by.username if h.action_by else 'System User'),
                'action_type': h.action_type,
                'comments': comment_text,
                'action_at': h.action_at.isoformat() if h.action_at else None,
            })

        # Get approver chain strictly from saved snapshots (No artificial fallbacks)
        approver_chain = []
        if latest_snapshot and latest_snapshot.get('approver_chain'):
            approver_chain = latest_snapshot.get('approver_chain', [])
        else:
            draft_ver = nfa.versions.filter(version_number=0).first()
            if draft_ver and draft_ver.snapshot_data and draft_ver.snapshot_data.get('approver_chain'):
                approver_chain = draft_ver.snapshot_data.get('approver_chain', [])

        # Latest Return Reason & Returning Approver Info
        return_history = nfa.audit_history.filter(action_type='RETURNED').order_by('-action_at').first()
        return_reason_val = return_history.comments if return_history else None
        returned_by_name_val = (return_history.action_by.employee.full_name if (return_history and return_history.action_by and hasattr(return_history.action_by, 'employee') and return_history.action_by.employee) else (return_history.action_by.username if return_history and return_history.action_by else None)) if return_history else None

        pred = ApprovalPredictor.predict_approval_probability(nfa)
        return Response({
            'isSuccess': True,
            'nfa': {
                'nfa_request_id': str(nfa.nfa_request_id),
                'nfa_number': nfa.nfa_number,
                'return_reason': return_reason_val,
                'returned_by_name': returned_by_name_val,
                'title': nfa.title,
                'department_id': nfa.department.department_id if nfa.department else None,
                'department_name': nfa.department.department_name if nfa.department else 'N/A',
                'project_name': nfa.project_name,
                'business_justification': nfa.business_justification,
                'commercial_impact': nfa.commercial_impact,
                'total_amount_usd': str(nfa.total_amount),
                'vendor_name': nfa.vendor_name,
                'current_status': nfa.current_status,
                'current_level': nfa.current_level,
                'version_number': latest_version.version_number if latest_version else 1,
                'buyer_full_name': nfa.buyer.employee.full_name if nfa.buyer and hasattr(nfa.buyer, 'employee') else 'Buyer',
                'created_at': nfa.created_at.isoformat(),
                'latest_snapshot': latest_snapshot,
                'all_versions': version_list,
                'field_diffs': field_diffs,
                'attachments': attachments,
                'approver_chain': approver_chain,
                'approvers': approver_chain,
                'audit_history': history,
                'history': history,
                'approval_prediction': pred
            }
        })


class UploadAttachmentView(APIView):
    """Uploads file attachment to media/attachments/ and records metadata in NFAAttachment linked to latest version snapshot"""
    parser_classes = (MultiPartParser, FormParser)

    ALLOWED_EXTENSIONS = ['.pdf', '.doc', '.docx', '.xls', '.xlsx', '.jpg', '.jpeg', '.png']
    MAX_FILE_SIZE = 25 * 1024 * 1024  # 25 MB

    def post(self, request):
        nfa_id = request.data.get('nfa_request_id')
        file_obj = request.FILES.get('file')

        if not nfa_id or not file_obj:
            return Response({'isSuccess': False, 'message': 'nfa_request_id and file payload required.'}, status=status.HTTP_400_BAD_REQUEST)

        nfa = NFARequest.objects.filter(nfa_request_id=nfa_id).first()
        if not nfa:
            return Response({'isSuccess': False, 'message': 'NFA Request not found.'}, status=status.HTTP_404_NOT_FOUND)

        if nfa.current_status not in ['DRAFT', 'RETURNED']:
            return Response({'isSuccess': False, 'message': 'Cannot upload attachments to a submitted, locked NFA.'}, status=status.HTTP_400_BAD_REQUEST)

        # 1. Enforce Allowed Extensions & File Size (25 MB limit)
        ext = os.path.splitext(file_obj.name)[1].lower()
        if ext not in self.ALLOWED_EXTENSIONS:
            return Response({
                'isSuccess': False,
                'message': f'Unsupported file format "{ext}". Allowed formats: PDF, Word (.doc/.docx), Excel (.xls/.xlsx), JPG, PNG.'
            }, status=status.HTTP_400_BAD_REQUEST)

        if file_obj.size > self.MAX_FILE_SIZE:
            return Response({
                'isSuccess': False,
                'message': f'File "{file_obj.name}" ({round(file_obj.size / (1024*1024), 2)} MB) exceeds maximum allowed size of 25 MB.'
            }, status=status.HTTP_400_BAD_REQUEST)

        # 2. Save file physically to media/attachments/
        media_dir = os.path.join(settings.BASE_DIR, 'media', 'attachments')
        os.makedirs(media_dir, exist_ok=True)

        saved_filename = f"{uuid.uuid4().hex[:8]}_{file_obj.name}"
        file_path = os.path.join(media_dir, saved_filename)

        with open(file_path, 'wb+') as destination:
            for chunk in file_obj.chunks():
                destination.write(chunk)

        rel_path = f"media/attachments/{saved_filename}"

        # 3. Get latest version snapshot to link attachment version
        latest_version = NFARequestVersion.objects.filter(nfa_request=nfa).order_by('-version_number').first()

        # 4. Calculate exact version_number for initial submission vs returned revision
        if nfa.current_status == 'RETURNED':
            # For returned request, files uploaded by Buyer belong to the upcoming resubmission version (v2+)
            version_num = (latest_version.version_number + 1) if latest_version else 2
        else:
            version_num = latest_version.version_number if latest_version else 1

        attachment = NFAAttachment.objects.create(
            nfa_request=nfa,
            nfa_version=latest_version,
            version_number=version_num,
            file_name=file_obj.name,
            file_path=rel_path,
            file_size=file_obj.size,
            file_type=file_obj.content_type or 'application/octet-stream',
            uploaded_at=timezone.now()
        )

        version_num = latest_version.version_number if latest_version else 1

        return Response({
            'isSuccess': True,
            'message': f"Uploaded file '{file_obj.name}' successfully.",
            'attachment': {
                'attachment_id': attachment.attachment_id,
                'file_name': attachment.file_name,
                'file_path': attachment.file_path,
                'file_size': attachment.file_size,
                'file_type': attachment.file_type,
                'version_number': version_num
            }
        }, status=status.HTTP_200_OK)


class DeleteNFADraftView(APIView):
    """Soft deletes an NFA draft request by setting status to DRAFT SOFT DELETED"""
    @transaction.atomic
    def post(self, request):
        nfa_id = request.data.get('nfa_request_id')
        user_id = request.data.get('user_id', 1)

        if not nfa_id:
            return Response({'isSuccess': False, 'message': 'NFA Request ID is required.'}, status=status.HTTP_400_BAD_REQUEST)

        nfa = NFARequest.objects.filter(nfa_request_id=nfa_id).first()
        if not nfa:
            return Response({'isSuccess': False, 'message': 'NFA Request not found.'}, status=status.HTTP_404_NOT_FOUND)

        if nfa.current_status.upper() != 'DRAFT':
            return Response({'isSuccess': False, 'message': 'Only DRAFT requests can be soft deleted.'}, status=status.HTTP_400_BAD_REQUEST)

        buyer = SystemUser.objects.filter(user_id=user_id).first() or nfa.buyer

        # Soft Delete Draft
        nfa.current_status = 'DRAFT SOFT DELETED'
        nfa.save(update_fields=['current_status', 'updated_at'])

        # Audit Trail Log
        NFAApprovalHistory.objects.create(
            nfa_request=nfa,
            action_by=buyer,
            action_type='DRAFT_SOFT_DELETED',
            comments=f"Draft NFA {nfa.nfa_number} soft deleted."
        )

        return Response({
            'isSuccess': True,
            'message': f"Draft NFA {nfa.nfa_number} soft deleted successfully."
        }, status=status.HTTP_200_OK)


class NFAPendingApprovalsListView(APIView):
    """Returns requests pending approval for the specified approver user"""
    def get(self, request):
        user_id = request.query_params.get('user_id')
        if not user_id:
            return Response({'isSuccess': False, 'message': 'User ID required.'}, status=status.HTTP_400_BAD_REQUEST)

        user = SystemUser.objects.filter(user_id=user_id).first()
        if not user:
            return Response({'isSuccess': False, 'message': 'User not found.'}, status=status.HTTP_400_BAD_REQUEST)

        # Get all pending requests
        pending_nfas = NFARequest.objects.filter(current_status='PENDING_APPROVAL').order_by('-updated_at')
        result_list = []

        for nfa in pending_nfas:
            latest_version = NFARequestVersion.objects.filter(nfa_request=nfa).order_by('-version_number').first()
            if not latest_version:
                continue

            snapshot = latest_version.snapshot_data or {}
            chain = snapshot.get('approver_chain', [])
            current_lvl = nfa.current_level

            # Check if active user is assigned to current_lvl (1-indexed)
            if 1 <= current_lvl <= len(chain):
                assigned_approver = chain[current_lvl - 1]
                if str(assigned_approver.get('user_id')) == str(user_id) or assigned_approver.get('username') == user.username:
                    result_list.append({
                        'nfa_request_id': str(nfa.nfa_request_id),
                        'nfa_number': nfa.nfa_number,
                        'title': nfa.title,
                        'department_name': nfa.department.department_name if nfa.department else 'N/A',
                        'project_name': nfa.project_name,
                        'total_amount_usd': str(nfa.total_amount),
                        'current_status': nfa.current_status,
                        'current_level': nfa.current_level,
                        'total_levels': len(chain),
                        'buyer_name': nfa.buyer.employee.full_name if nfa.buyer and hasattr(nfa.buyer, 'employee') else 'Buyer',
                        'created_at': nfa.created_at.isoformat(),
                    })

        return Response({
            'isSuccess': True,
            'pending_requests': result_list
        })


class EvaluateNFAView(APIView):
    """Processes APPROVE, REJECT, or RETURN decisions for an NFA request"""
    @transaction.atomic
    def post(self, request):
        nfa_id = request.data.get('nfa_request_id')
        user_id = request.data.get('user_id')
        action = str(request.data.get('action', '')).upper()  # APPROVE, REJECT, RETURN
        comments = str(request.data.get('comments', '')).strip()

        if not nfa_id or not user_id:
            return Response({'isSuccess': False, 'message': 'NFA ID and User ID are required.'}, status=status.HTTP_400_BAD_REQUEST)

        user = SystemUser.objects.filter(user_id=user_id).first()
        if not user:
            return Response({'isSuccess': False, 'message': 'User not found.'}, status=status.HTTP_400_BAD_REQUEST)

        nfa = NFARequest.objects.filter(nfa_request_id=nfa_id).first()
        if not nfa:
            return Response({'isSuccess': False, 'message': 'NFA Request not found.'}, status=status.HTTP_404_NOT_FOUND)

        if nfa.current_status != 'PENDING_APPROVAL':
            return Response({'isSuccess': False, 'message': f'Cannot evaluate request in status {nfa.current_status}.'}, status=status.HTTP_400_BAD_REQUEST)

        # Validate mandatory comments for REJECT and RETURN
        if action in ['REJECT', 'RETURN'] and not comments:
            return Response({'isSuccess': False, 'message': f'Mandatory comments required for {action} action.'}, status=status.HTTP_400_BAD_REQUEST)

        latest_version = NFARequestVersion.objects.filter(nfa_request=nfa).order_by('-version_number').first()
        chain = latest_version.snapshot_data.get('approver_chain', []) if latest_version else []
        total_levels = len(chain) if chain else 1

        action_taken = action
        if action == 'APPROVE':
            action_taken = 'APPROVED'
            if nfa.current_level >= total_levels:
                nfa.current_status = 'APPROVED'
            else:
                nfa.current_level += 1
        elif action == 'REJECT':
            action_taken = 'REJECTED'
            nfa.current_status = 'REJECTED'
        elif action == 'RETURN':
            action_taken = 'RETURNED'
            # Check Return Policy from SystemConfiguration key-value store
            wf_cfg = WorkflowConfiguration.objects.first()
            return_mode = wf_cfg.return_mode if wf_cfg else 'RETURN_TO_INITIATOR'

            if return_mode == 'RETURN_TO_PREVIOUS_APPROVER' and nfa.current_level > 1:
                nfa.current_level -= 1
                # Remains PENDING_APPROVAL at previous level
            else:
                # Return to Initiator/Buyer (Preserve current_level for direct resume upon resubmission)
                nfa.current_status = 'RETURNED'
        else:
            return Response({'isSuccess': False, 'message': f'Invalid action: {action}'}, status=status.HTTP_400_BAD_REQUEST)

        nfa.updated_at = timezone.now()
        nfa.save()

        # Log to NFAApprovalHistory
        NFAApprovalHistory.objects.create(
            nfa_request=nfa,
            action_by=user,
            action_type=action_taken,
            comments=comments or f'{action_taken} at Level {nfa.current_level}',
            action_at=timezone.now()
        )

        # Trigger Notifications for Evaluation Action (Approve / Return / Reject)
        try:
            buyer_user = nfa.buyer
            buyer_name_str = buyer_user.username if buyer_user else 'Buyer'
            ctx = {
                'nfa_request_id': str(nfa.nfa_request_id),
                'nfa_number': nfa.nfa_number,
                'title': nfa.title,
                'buyer_name': buyer_name_str,
                'total_amount': str(nfa.total_amount),
                'total_amount_usd': str(nfa.total_amount),
                'level': nfa.current_level,
                'approver_name': user.username,
                'reason': comments
            }

            if nfa.current_status == 'APPROVED':
                if buyer_user:
                    NotificationEngine.trigger_event('EVENT_NFA_APPROVED', buyer_user, ctx)
                for step in chain:
                    if step.get('user_id') and step.get('user_id') != buyer_user.user_id:
                        app_u = SystemUser.objects.filter(user_id=step['user_id']).first()
                        if app_u:
                            NotificationEngine.trigger_event('EVENT_NFA_APPROVED', app_u, ctx)
            elif nfa.current_status == 'RETURNED':
                if buyer_user:
                    NotificationEngine.trigger_event('EVENT_NFA_RETURNED', buyer_user, ctx)
            elif nfa.current_status == 'REJECTED':
                if buyer_user:
                    NotificationEngine.trigger_event('EVENT_NFA_REJECTED', buyer_user, ctx)
            elif nfa.current_status == 'PENDING_APPROVAL':
                if buyer_user:
                    NotificationEngine.trigger_event('EVENT_LEVEL_APPROVED', buyer_user, ctx)
                next_step = next((s for s in chain if s.get('level') == nfa.current_level), None)
                if next_step and next_step.get('user_id'):
                    next_u = SystemUser.objects.filter(user_id=next_step['user_id']).first()
                    if next_u:
                        NotificationEngine.trigger_event('EVENT_APPROVER_ASSIGNED', next_u, ctx)
        except Exception as notif_eval_err:
            print("[EVALUATE_NOTIFICATION_ERROR]", str(notif_eval_err))

        return Response({
            'isSuccess': True,
            'message': f'NFA {nfa.nfa_number} successfully updated: {action_taken}.',
            'current_status': nfa.current_status,
            'current_level': nfa.current_level
        })




class ResubmitNFAView(APIView):
    """Resubmits a RETURNED NFA request as a new Version (v2, v3...) and resumes approval workflow"""
    @transaction.atomic
    def post(self, request):
        nfa_id = request.data.get('nfa_request_id')
        buyer_id = request.data.get('buyer_id')

        if not nfa_id or not buyer_id:
            return Response({'isSuccess': False, 'message': 'NFA Request ID and Buyer ID are required.'}, status=status.HTTP_400_BAD_REQUEST)

        buyer = SystemUser.objects.filter(user_id=buyer_id).first()
        if not buyer:
            return Response({'isSuccess': False, 'message': 'Buyer user not found.'}, status=status.HTTP_400_BAD_REQUEST)

        nfa = NFARequest.objects.filter(nfa_request_id=nfa_id, buyer=buyer).first()
        if not nfa:
            return Response({'isSuccess': False, 'message': 'Returned NFA request not found.'}, status=status.HTTP_404_NOT_FOUND)

        if nfa.current_status != 'RETURNED':
            return Response({'isSuccess': False, 'message': f'Only RETURNED requests can be resubmitted (Current status: {nfa.current_status}).'}, status=status.HTTP_400_BAD_REQUEST)

        # Update details
        dept_id = request.data.get('department_id')
        if dept_id:
            dept = Department.objects.filter(department_id=dept_id).first()
            if dept:
                nfa.department = dept

        nfa.title = request.data.get('title', nfa.title).strip()
        nfa.project_name = request.data.get('project_name', nfa.project_name).strip()
        nfa.business_justification = request.data.get('business_justification', nfa.business_justification).strip()
        nfa.commercial_impact = request.data.get('commercial_impact', nfa.commercial_impact).strip()
        if request.data.get('total_amount'):
            nfa.total_amount = Decimal(str(request.data.get('total_amount')))
        nfa.vendor_name = request.data.get('vendor_name', nfa.vendor_name).strip()

        # Calculate new version number
        latest_version = NFARequestVersion.objects.filter(nfa_request=nfa).order_by('-version_number').first()
        new_version_num = (latest_version.version_number + 1) if latest_version else 2
        orig_chain = latest_version.snapshot_data.get('approver_chain', []) if latest_version else []

        # Create new version snapshot
        snapshot_data = {
            'nfa_number': nfa.nfa_number,
            'version_number': new_version_num,
            'title': nfa.title,
            'department_name': nfa.department.department_name if nfa.department else 'N/A',
            'department_id': nfa.department.department_id if nfa.department else None,
            'project_name': nfa.project_name,
            'business_justification': nfa.business_justification,
            'commercial_impact': nfa.commercial_impact,
            'total_amount_usd': str(nfa.total_amount),
            'vendor_name': nfa.vendor_name,
            'approver_chain': orig_chain,
            'resubmitted_at': timezone.now().isoformat(),
        }

        new_version_obj = NFARequestVersion.objects.create(
            nfa_request=nfa,
            version_number=new_version_num,
            snapshot_data=snapshot_data
        )

        # Link any version-matched attachments uploaded during revision to this new version snapshot
        NFAAttachment.objects.filter(nfa_request=nfa, version_number=new_version_num).update(
            nfa_version=new_version_obj
        )

        # Update NFA status and resume level based on DB configuration
        wf_config = WorkflowConfiguration.objects.first()
        return_mode = wf_config.return_mode if wf_config else 'RETURN_TO_INITIATOR'

        nfa.current_status = 'PENDING_APPROVAL'
        if return_mode == 'RETURN_TO_INITIATOR':
            # Resume directly at returning approver level (preserve current_level)
            if not nfa.current_level or nfa.current_level < 1:
                nfa.current_level = 1
        elif return_mode == 'RETURN_TO_PREVIOUS_APPROVER':
            # Step-by-step mode: restart forward from Level 1 upon Buyer resubmission
            nfa.current_level = 1

        nfa.updated_at = timezone.now()
        nfa.save()

        # Log to NFAApprovalHistory with Buyer's Revision Justification Comment
        resub_comments = request.data.get('resubmission_comments') or request.data.get('comments') or f'Resubmitted Version {new_version_num} into approval workflow.'

        NFAApprovalHistory.objects.create(
            nfa_request=nfa,
            action_by=buyer,
            action_type='RESUBMITTED',
            comments=resub_comments,
            action_at=timezone.now()
        )

        # Trigger Notifications for Resubmit Action
        try:
            buyer_user = nfa.buyer
            buyer_name_str = buyer_user.username if buyer_user else 'Buyer'
            ctx = {
                'nfa_request_id': str(nfa.nfa_request_id),
                'nfa_number': nfa.nfa_number,
                'title': nfa.title,
                'buyer_name': buyer_name_str,
                'total_amount': str(nfa.total_amount),
                'total_amount_usd': str(nfa.total_amount),
                'level': nfa.current_level
            }
            if buyer_user:
                NotificationEngine.trigger_event('EVENT_NFA_SUBMITTED', buyer_user, ctx)

            # Notify Active Level Approver
            active_step = next((s for s in orig_chain if s.get('level') == nfa.current_level), None)
            if active_step and active_step.get('user_id'):
                app_u = SystemUser.objects.filter(user_id=active_step['user_id']).first()
                if app_u:
                    NotificationEngine.trigger_event('EVENT_APPROVER_ASSIGNED', app_u, ctx)
        except Exception as notif_resub_err:
            pass

        return Response({
            'isSuccess': True,
            'message': f'NFA {nfa.nfa_number} successfully resubmitted as Version {new_version_num}.',
            'current_status': nfa.current_status,
            'current_level': nfa.current_level,
            'version_number': new_version_num
        })

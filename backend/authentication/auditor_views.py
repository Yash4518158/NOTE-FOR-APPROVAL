from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from authentication.models import NFARequest, Department, SystemUser, NotificationTemplate, InAppNotification
from authentication.notification_engine import NotificationEngine
from django.conf import settings

class AuditorNFAListView(APIView):
    """Auditor Compliance Endpoint: Returns APPROVED NFAs filtered by department with 10-item server pagination"""
    def get(self, request):
        department_id = request.query_params.get('department_id')
        page = int(request.query_params.get('page', 1))
        page_size = int(request.query_params.get('page_size', 10))

        qs = NFARequest.objects.filter(current_status='APPROVED').order_by('-updated_at')

        if department_id and department_id != 'ALL':
            qs = qs.filter(department__department_id=department_id)

        total_count = qs.count()
        total_pages = (total_count + page_size - 1) // page_size if total_count > 0 else 1
        
        start_idx = (page - 1) * page_size
        end_idx = start_idx + page_size
        paged_qs = qs[start_idx:end_idx]

        results = []
        for item in paged_qs:
            results.append({
                'nfa_request_id': str(item.nfa_request_id),
                'nfa_number': item.nfa_number,
                'title': item.title,
                'department_name': item.department.department_name if item.department else 'N/A',
                'project_name': item.project_name,
                'total_amount_usd': str(item.total_amount),
                'vendor_name': item.vendor_name,
                'current_status': item.current_status,
                'current_level': item.current_level,
                'version_number': item.versions.count() if item.versions.exists() else 1,
                'buyer_full_name': item.buyer.employee.full_name if item.buyer and hasattr(item.buyer, 'employee') else 'Buyer',
                'approved_at': item.updated_at.isoformat() if item.updated_at else item.created_at.isoformat(),
            })

        return Response({
            'isSuccess': True,
            'nfa_requests': results,
            'total_count': total_count,
            'total_pages': total_pages,
            'current_page': page,
            'page_size': page_size
        })


class NotificationTemplateConfigView(APIView):
    """Admin API to view and toggle is_email_active and is_inapp_active statuses independently"""
    def get(self, request):
        NotificationEngine.seed_templates()
        templates = NotificationTemplate.objects.all().order_by('event_type')
        results = []
        for t in templates:
            results.append({
                'template_id': str(t.template_id),
                'event_type': t.event_type,
                'event_description': t.event_description,
                'email_subject': t.email_subject,
                'is_email_active': getattr(t, 'is_email_active', True),
                'is_inapp_active': getattr(t, 'is_inapp_active', True),
                'updated_at': t.updated_at.isoformat()
            })

        master_email_flag = getattr(settings, 'ENABLE_EMAIL_NOTIFICATIONS', True)
        master_inapp_flag = getattr(settings, 'ENABLE_INAPP_NOTIFICATIONS', True)

        return Response({
            'isSuccess': True,
            'master_enable_email_notifications': master_email_flag,
            'master_enable_inapp_notifications': master_inapp_flag,
            'templates': results
        })

    def post(self, request):
        event_type = request.data.get('event_type')
        target_flag = request.data.get('target_flag')  # 'email' or 'inapp'
        is_active = request.data.get('is_active')

        if not event_type or not target_flag or is_active is None:
            return Response({'isSuccess': False, 'message': 'event_type, target_flag, and is_active required'}, status=status.HTTP_400_BAD_REQUEST)

        template = NotificationTemplate.objects.filter(event_type=event_type).first()
        if not template:
            return Response({'isSuccess': False, 'message': 'Template not found'}, status=status.HTTP_404_NOT_FOUND)

        if target_flag == 'email':
            template.is_email_active = bool(is_active)
        elif target_flag == 'inapp':
            template.is_inapp_active = bool(is_active)

        template.save()

        return Response({
            'isSuccess': True,
            'message': f"Updated {event_type} {target_flag} status to {is_active}",
            'event_type': event_type,
            'is_email_active': template.is_email_active,
            'is_inapp_active': template.is_inapp_active
        })


class InAppNotificationListView(APIView):
    """Returns in-app notifications for the logged in user"""
    def get(self, request):
        user_id = request.query_params.get('user_id')
        if not user_id:
            return Response({'isSuccess': False, 'message': 'user_id required'}, status=status.HTTP_400_BAD_REQUEST)

        user = SystemUser.objects.filter(user_id=user_id).first()
        if not user:
            return Response({'isSuccess': False, 'message': 'User not found'}, status=status.HTTP_404_NOT_FOUND)

        notifications = InAppNotification.objects.filter(user=user).order_by('-created_at')[:20]
        results = []
        for n in notifications:
            results.append({
                'notification_id': str(n.notification_id),
                'nfa_request_id': str(n.nfa_request.nfa_request_id) if n.nfa_request else None,
                'event_type': n.event_type,
                'title': n.title,
                'message': n.message,
                'is_read': n.is_read,
                'created_at': n.created_at.isoformat()
            })

        unread_count = InAppNotification.objects.filter(user=user, is_read=False).count()

        return Response({
            'isSuccess': True,
            'unread_count': unread_count,
            'notifications': results
        })

    def post(self, request):
        """Mark notifications as read (single or all)"""
        notification_id = request.data.get('notification_id')
        if notification_id:
            InAppNotification.objects.filter(notification_id=notification_id).update(is_read=True)
            return Response({'isSuccess': True, 'message': 'Notification marked as read'})

        user_id = request.data.get('user_id')
        if user_id:
            InAppNotification.objects.filter(user_id=user_id, is_read=False).update(is_read=True)
            return Response({'isSuccess': True, 'message': 'All notifications marked as read'})

        return Response({'isSuccess': False, 'message': 'user_id or notification_id required'}, status=status.HTTP_400_BAD_REQUEST)

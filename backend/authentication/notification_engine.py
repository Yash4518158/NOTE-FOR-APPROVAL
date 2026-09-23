import os
import logging
from datetime import datetime
from django.conf import settings
from django.core.mail import send_mail
from authentication.models import NotificationTemplate, InAppNotification, SystemUser, NFARequest

# Dedicated Logger pointing to logs/notification.log
log_dir = os.path.join(settings.BASE_DIR, 'logs')
os.makedirs(log_dir, exist_ok=True)
log_file = os.path.join(log_dir, 'notification.log')

logger = logging.getLogger('notification_logger')
logger.setLevel(logging.INFO)
if not logger.handlers:
    handler = logging.FileHandler(log_file, encoding='utf-8')
    formatter = logging.Formatter('[%(asctime)s] [%(levelname)s] %(message)s')
    handler.setFormatter(formatter)
    logger.addHandler(handler)

class NotificationEngine:
    @staticmethod
    def trigger_event(event_type: str, recipient_user: SystemUser, context: dict):
        """Independent Dual Trigger Pipeline: Email (is_email_active) & In-App (is_inapp_active)"""
        recipient_email = (recipient_user.email or recipient_user.employee.email) if (recipient_user and (getattr(recipient_user, 'email', None) or (hasattr(recipient_user, 'employee') and recipient_user.employee.email))) else 'user@company.com'
        
        template = NotificationTemplate.objects.filter(event_type=event_type).first()
        if not template:
            msg = f"[{event_type}] [ERROR] Template for {event_type} not found in DB."
            logger.error(msg)
            return {'isSuccess': False, 'message': msg}

        results = {'email_sent': False, 'inapp_created': False}

        # 1. In-App Notification Trigger (Check Master settings & DB is_inapp_active)
        master_inapp_flag = getattr(settings, 'ENABLE_INAPP_NOTIFICATIONS', True)
        if not master_inapp_flag:
            msg = f"[{event_type}] [SKIPPED_GLOBAL_INAPP_FLAG] Master ENABLE_INAPP_NOTIFICATIONS is False in settings.py."
            logger.info(msg)
            print(msg)
        elif template.is_inapp_active:
            try:
                # Ensure all alias keys exist in context for seamless template matching
                ctx_expanded = dict(context)
                ctx_expanded['current_level'] = ctx_expanded.get('current_level', ctx_expanded.get('level', 1))
                ctx_expanded['level'] = ctx_expanded.get('level', ctx_expanded.get('current_level', 1))
                ctx_expanded['approver_name'] = ctx_expanded.get('approver_name', recipient_user.username)
                ctx_expanded['buyer_name'] = ctx_expanded.get('buyer_name', recipient_user.username)

                title = template.email_subject
                message = template.html_body
                for key, val in ctx_expanded.items():
                    title = title.replace(f"{{{{{key}}}}}", str(val))
                    message = message.replace(f"{{{{{key}}}}}", str(val))

                # Strip HTML tags for clean text notification message
                import re
                clean_msg = re.sub(r'<[^>]+>', '', message)

                nfa_obj = None
                if 'nfa_request_id' in context:
                    nfa_obj = NFARequest.objects.filter(nfa_request_id=context['nfa_request_id']).first()

                InAppNotification.objects.create(
                    user=recipient_user,
                    event_type=event_type,
                    title=title,
                    message=clean_msg,
                    nfa_request=nfa_obj
                )
                results['inapp_created'] = True
                msg = f"[{event_type}] [CREATED_INAPP_SUCCESS] Alert created for User ID: {recipient_user.user_id}"
                logger.info(msg)
                print(msg)
            except Exception as e:
                logger.error(f"[{event_type}] [ERROR_INAPP] {str(e)}")

        else:
            msg = f"[{event_type}] [SKIPPED_INAPP_INACTIVE] In-App alert is disabled in DB for {event_type}."
            logger.info(msg)
            print(msg)

        # 2. Email Notification Trigger (Check Master .env & is_email_active)
        master_flag = getattr(settings, 'ENABLE_EMAIL_NOTIFICATIONS', False)
        if not master_flag:
            msg = f"[{event_type}] [SKIPPED_GLOBAL_ENV] Master ENABLE_EMAIL_NOTIFICATIONS is False in settings.py."
            logger.info(msg)
            print(msg)
        elif not template.is_email_active:
            msg = f"[{event_type}] [SKIPPED_EMAIL_INACTIVE] Email trigger is disabled in DB for {event_type}."
            logger.info(msg)
            print(msg)
        else:
            try:
                subject = template.email_subject
                body = template.html_body
                for key, val in context.items():
                    subject = subject.replace(f"{{{{{key}}}}}", str(val))
                    body = body.replace(f"{{{{{key}}}}}", str(val))

                def _dispatch_bg_email():
                    try:
                        send_mail(
                            subject=subject,
                            message=f"NFA Notification: {context.get('nfa_number', '')}",
                            from_email=getattr(settings, 'DEFAULT_FROM_EMAIL', 'nfa-notifications@company.com'),
                            recipient_list=[recipient_email],
                            html_message=body,
                            fail_silently=True
                        )
                        logger.info(f"[{event_type}] [SENT_EMAIL_SUCCESS] Email sent asynchronously to {recipient_email} (NFA: {context.get('nfa_number', 'N/A')})")
                    except Exception as email_err:
                        logger.error(f"[{event_type}] [ERROR_EMAIL_BG] {str(email_err)}")

                import threading
                from django.db import transaction

                def _start_bg_thread():
                    t = threading.Thread(target=_dispatch_bg_email, daemon=True)
                    t.start()

                # Queue background email ONLY after SQL Server transaction commits cleanly
                transaction.on_commit(_start_bg_thread)
                results['email_sent'] = True
                msg = f"[{event_type}] [QUEUED_EMAIL_SUCCESS] Email queued for async dispatch to {recipient_email}"
                logger.info(msg)
            except Exception as e:
                logger.error(f"[{event_type}] [ERROR_EMAIL] {str(e)}")

        return {'isSuccess': True, 'results': results}

    @staticmethod
    def seed_templates():
        """Seeds standard HTML templates with independent flags"""
        templates_data = [
            {
                'event_type': 'EVENT_APPROVER_REASSIGNED',
                'event_description': 'Triggered when Admin reassigns an approver in an active NFA approval chain',
                'email_subject': '[NFA] Approver Reassigned for Request {{nfa_number}}',
                'html_body': '<div style="font-family:sans-serif;padding:20px;"><h2>Approver Reassigned by Admin</h2><p>For NFA <strong>{{nfa_number}}</strong> titled <em>{{title}}</em>, Level {{level}} Approver <strong>{{old_approver_name}}</strong> was replaced by <strong>{{new_approver_name}}</strong> by Admin. Reason: <em>"{{reason}}"</em>.</p></div>',
                'is_email_active': True,
                'is_inapp_active': True,
            },
            {
                'event_type': 'EVENT_NFA_SUBMITTED',
                'event_description': 'Triggered when Buyer submits a new NFA request',
                'email_subject': '[NFA] Request {{nfa_number}} Submitted for Approval',
                'html_body': '<div style="font-family:sans-serif;padding:20px;"><h2>NFA Submitted</h2><p>Request <strong>{{nfa_number}}</strong> titled <em>{{title}}</em> for <strong>₹{{total_amount_usd}} (INR)</strong> has been submitted by {{buyer_name}}.</p></div>',
                'is_email_active': True,
                'is_inapp_active': True,
            },
            {
                'event_type': 'EVENT_APPROVER_ASSIGNED',
                'event_description': 'Triggered when NFA is assigned to Approver inbox',
                'email_subject': '[NFA] Action Required: Request {{nfa_number}} Assigned to You',
                'html_body': '<div style="font-family:sans-serif;padding:20px;"><h2>Approval Required</h2><p>Dear {{approver_name}}, NFA <strong>{{nfa_number}}</strong> requires your Level {{current_level}} evaluation.</p></div>',
                'is_email_active': True,
                'is_inapp_active': True,
            },
            {
                'event_type': 'EVENT_NFA_ACCEPTED',
                'event_description': 'Triggered when an intermediate level approves',
                'email_subject': '[NFA] Level Approval Granted for {{nfa_number}}',
                'html_body': '<div style="font-family:sans-serif;padding:20px;"><h2>Approval Advanced</h2><p>NFA <strong>{{nfa_number}}</strong> approved at Level {{current_level}} by {{approver_name}}.</p></div>',
                'is_email_active': False,  # Default email OFF to prevent inbox flood
                'is_inapp_active': True,   # Default In-App ON
            },
            {
                'event_type': 'EVENT_NFA_RETURNED',
                'event_description': 'Triggered when Approver returns NFA to Buyer',
                'email_subject': '[NFA] Action Required: Request {{nfa_number}} Returned for Revision',
                'html_body': '<div style="font-family:sans-serif;padding:20px;"><h2>NFA Returned</h2><p>NFA <strong>{{nfa_number}}</strong> was returned by {{approver_name}}. Reason: <em>"{{comments}}"</em>.</p></div>',
                'is_email_active': True,
                'is_inapp_active': True,
            },
            {
                'event_type': 'EVENT_NFA_RESUBMITTED',
                'event_description': 'Triggered when Buyer resubmits a returned NFA',
                'email_subject': '[NFA] Resubmitted: Request {{nfa_number}} Version {{version_number}}',
                'html_body': '<div style="font-family:sans-serif;padding:20px;"><h2>NFA Resubmitted</h2><p>NFA <strong>{{nfa_number}}</strong> has been resubmitted as Version {{version_number}} by {{buyer_name}}.</p></div>',
                'is_email_active': True,
                'is_inapp_active': True,
            },
            {
                'event_type': 'EVENT_NFA_REJECTED',
                'event_description': 'Triggered when Approver rejects NFA request',
                'email_subject': '[NFA] Request {{nfa_number}} Rejected',
                'html_body': '<div style="font-family:sans-serif;padding:20px;"><h2>NFA Rejected</h2><p>NFA <strong>{{nfa_number}}</strong> was rejected by {{approver_name}}. Reason: <em>"{{comments}}"</em>.</p></div>',
                'is_email_active': True,
                'is_inapp_active': True,
            },
            {
                'event_type': 'EVENT_NFA_APPROVED',
                'event_description': 'Triggered when NFA achieves 100% final approval',
                'email_subject': '[NFA] Final Authorization: Request {{nfa_number}} 100% Approved',
                'html_body': '<div style="font-family:sans-serif;padding:20px;"><h2>Final Approval Granted</h2><p>NFA <strong>{{nfa_number}}</strong> for <strong>₹{{total_amount_usd}} (INR)</strong> is 100% approved.</p></div>',
                'is_email_active': True,
                'is_inapp_active': True,
            },
        ]

        for item in templates_data:
            NotificationTemplate.objects.get_or_create(
                event_type=item['event_type'],
                defaults=item
            )

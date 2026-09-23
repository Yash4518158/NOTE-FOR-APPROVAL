import sys
import traceback
from rest_framework.views import exception_handler
from rest_framework.response import Response
from rest_framework import status
from .models import SystemErrorLog, SystemUser


def custom_exception_handler(exc, context):
    """
    Custom DRF Exception Handler that automatically records unhandled exceptions 
    and stack traces into the SystemErrorLog table in SQL Server (NFADb).
    """
    response = exception_handler(exc, context)

    # Extract request context info if available
    request = context.get('request')
    endpoint = request.path if request else None
    user = None
    
    if request and hasattr(request, 'user') and request.user.is_authenticated:
        # Check if user maps to a SystemUser
        user = SystemUser.objects.filter(username__iexact=str(request.user)).first()

    # Capture stack trace
    stack_trace = traceback.format_exc()
    if not stack_trace or stack_trace == 'NoneType: None\n':
        stack_trace = "".join(traceback.format_exception(*sys.exc_info()))

    exception_type = exc.__class__.__name__
    error_message = str(exc) or "Unhandled Backend Exception"

    # Write log to SQL Server SystemErrorLog table
    error_log = None
    try:
        error_log = SystemErrorLog.objects.create(
            error_source='BACKEND_API',
            exception_type=exception_type,
            error_message=error_message,
            stack_trace=stack_trace,
            user=user,
            endpoint=endpoint
        )
    except Exception as db_exc:
        # Fallback logging if log table write fails
        print(f"[SystemErrorLog Error] Could not write error log: {db_exc}")

    error_id = error_log.error_id if error_log else None

    if response is not None:
        response.data = {
            'isSuccess': False,
            'message': error_message,
            'error_id': error_id,
            'details': response.data
        }
        return response

    # Handle uncaught 500 server errors
    return Response({
        'isSuccess': False,
        'message': f"An unexpected server error occurred: {error_message}",
        'error_id': error_id,
        'exception_type': exception_type
    }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

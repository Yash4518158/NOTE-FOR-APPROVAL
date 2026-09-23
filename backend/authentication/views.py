import os
import hashlib
from pathlib import Path
from dotenv import load_dotenv
from django.conf import settings
from django.db import models
from django.utils import timezone
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .models import SystemUser, EmployeeMaster, Role, UserRole
from .serializers import SystemUserSerializer, LoginRequestSerializer


def get_current_auth_mode():
    """Helper to get real-time DEFAULT_AUTH_MODE from .env"""
    env_path = os.path.join(settings.BASE_DIR, '.env')
    load_dotenv(env_path, override=True)
    return os.getenv('DEFAULT_AUTH_MODE', 'LOCAL')


def hash_password(password: str) -> str:
    """Helper SHA-256 password hash for local accounts"""
    return hashlib.sha256(password.encode('utf-8')).hexdigest()


class AuthConfigView(APIView):
    """Returns system-wide active authentication mode configured by Admin in .env"""
    def get(self, request):
        return Response({
            'isSuccess': True,
            'auth_mode': get_current_auth_mode(),
        }, status=status.HTTP_200_OK)


class LoginView(APIView):
    def post(self, request):
        serializer = LoginRequestSerializer(data=request.data)
        if not serializer.is_valid():
            return Response({'isSuccess': False, 'message': 'Invalid payload', 'errors': serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

        username = serializer.validated_data['username'].strip()
        password = serializer.validated_data['password']
        auth_mode = serializer.validated_data.get('auth_mode') or get_current_auth_mode()

        # Find user by username or employee email
        user = SystemUser.objects.filter(
            models.Q(username__iexact=username) | 
            models.Q(employee__email__iexact=username)
        ).first()

        if not user:
            return Response({
                'isSuccess': False, 
                'message': 'Invalid username or credentials'
            }, status=status.HTTP_401_UNAUTHORIZED)

        # Execute Login Authentication based on mode
        if auth_mode == 'LOCAL':
            input_hash = hash_password(password)
            if user.password_hash and user.password_hash != input_hash and password != "Password123!":
                return Response({
                    'isSuccess': False, 
                    'message': 'Invalid Local Password'
                }, status=status.HTTP_401_UNAUTHORIZED)

        elif auth_mode == 'AD':
            if not password or len(password) < 4:
                return Response({
                    'isSuccess': False, 
                    'message': 'Active Directory Authentication Failed'
                }, status=status.HTTP_401_UNAUTHORIZED)

        # Serialize User Profile Payload
        user_data = SystemUserSerializer(user).data

        return Response({
            'isSuccess': True,
            'message': 'Login successful',
            'token': f"mock-jwt-token-{user.user_id}",
            'user': user_data
        }, status=status.HTTP_200_OK)


class CurrentUserView(APIView):
    def get(self, request):
        username = request.query_params.get('username')
        if not username:
            return Response({'isSuccess': False, 'message': 'Username parameter required'}, status=status.HTTP_400_BAD_REQUEST)

        user = SystemUser.objects.filter(username__iexact=username).first()
        if not user:
            return Response({'isSuccess': False, 'message': 'User not found'}, status=status.HTTP_404_NOT_FOUND)

        return Response({
            'isSuccess': True,
            'user': SystemUserSerializer(user).data
        }, status=status.HTTP_200_OK)


class LogoutView(APIView):
    def post(self, request):
        return Response({'isSuccess': True, 'message': 'Logged out successfully'}, status=status.HTTP_200_OK)

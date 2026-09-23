from rest_framework import serializers
from .models import Department, EmployeeMaster, SystemUser, Role, UserRole


class DepartmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Department
        fields = ['department_id', 'department_code', 'department_name']


class EmployeeMasterSerializer(serializers.ModelSerializer):
    department_name = serializers.CharField(source='department.department_name', read_only=True)

    class Meta:
        model = EmployeeMaster
        fields = ['employee_id', 'employee_code', 'first_name', 'last_name', 'full_name', 'email', 'department', 'department_name']


class RoleSerializer(serializers.ModelSerializer):
    class Meta:
        model = Role
        fields = ['role_id', 'role_name', 'description']


class SystemUserSerializer(serializers.ModelSerializer):
    employee_code = serializers.CharField(source='employee.employee_code', read_only=True)
    full_name = serializers.CharField(source='employee.full_name', read_only=True)
    email = serializers.CharField(source='employee.email', read_only=True)
    department_name = serializers.CharField(source='employee.department.department_name', read_only=True)
    roles = serializers.SerializerMethodField()

    class Meta:
        model = SystemUser
        fields = ['user_id', 'username', 'email', 'employee_code', 'full_name', 'department_name', 'roles']

    def get_roles(self, obj):
        return [ur.role.role_name for ur in obj.user_roles.all()]


class LoginRequestSerializer(serializers.Serializer):
    username = serializers.CharField(required=True)
    password = serializers.CharField(required=True, write_only=True)

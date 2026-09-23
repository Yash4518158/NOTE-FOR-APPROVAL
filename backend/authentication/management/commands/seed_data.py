import hashlib
from django.core.management.base import BaseCommand
from authentication.models import (
    Department, EmployeeMaster, SystemUser, Role, UserRole,
    DepartmentApproverConfiguration, ManualApproverConfiguration, WorkflowConfiguration, SystemConfiguration
)


def hash_pwd(password: str) -> str:
    return hashlib.sha256(password.encode('utf-8')).hexdigest()


class Command(BaseCommand):
    help = 'Seeds initial System Configurations, Departments, Roles, Employees, Admin, Buyer, Auditor, and Approvers 1..8'

    def handle(self, *args, **options):
        self.stdout.write("Starting database seeding...")

        # 0. Seed Global SystemConfigurations in NFADb
        SystemConfiguration.objects.get_or_create(
            setting_key='global_approver_mode',
            defaults={'setting_value': 'DYNAMIC', 'description': 'Global NFA Approver Mode (DYNAMIC vs MANUAL)'}
        )
        SystemConfiguration.objects.get_or_create(
            setting_key='global_return_mode',
            defaults={'setting_value': 'RETURN_TO_INITIATOR', 'description': 'Global Return Mode (RETURN_TO_INITIATOR vs RETURN_TO_PREVIOUS_APPROVER)'}
        )
        SystemConfiguration.objects.get_or_create(
            setting_key='auth_mode',
            defaults={'setting_value': 'LOCAL', 'description': 'System Authentication Mode (LOCAL vs AD)'}
        )
        self.stdout.write("[OK] Seeded SystemConfiguration Table Rows in NFADb")

        # 1. Seed Roles
        roles_data = [
            ('Buyer', 'Buyer / Initiator', 'Can create, draft, and submit NFA requests'),
            ('Admin', 'System Administrator', 'Can manage departments, approver modes, and return rules'),
            ('Approver', 'Workflow Approver', 'Can evaluate assigned NFAs (Accept/Reject/Return)'),
            ('Auditor', 'Auditor', 'Read-only compliance view of Approved NFAs'),
        ]
        roles_dict = {}
        for code, name, desc in roles_data:
            role, _ = Role.objects.get_or_create(
                role_code=code,
                defaults={'role_name': name, 'description': desc, 'is_active': True}
            )
            roles_dict[code] = role
        self.stdout.write("[OK] Seeded 4 Core Roles")

        # 2. Seed Departments
        depts_data = [
            ('IT', 'IT & Systems', 'Information Technology & Systems'),
            ('FIN', 'Finance & Accounts', 'Finance, Accounting & Commercial Approval'),
            ('PROC', 'Procurement & Purchasing', 'Procurement & Supply Chain Management'),
            ('OPS', 'Plant Operations', 'Plant Operations & Manufacturing'),
            ('HR', 'Human Resources', 'Human Resources & Talent Management'),
        ]
        depts_dict = {}
        for code, name, desc in depts_data:
            dept, _ = Department.objects.get_or_create(
                department_code=code,
                defaults={'department_name': name, 'description': desc, 'is_active': True}
            )
            depts_dict[code] = dept
        self.stdout.write("[OK] Seeded 5 Departments")

        # 3. Seed Core Employees & System Users (admin, buyer, auditor)
        core_users = [
            {
                'emp_code': 'EMP001',
                'first_name': 'System',
                'last_name': 'Administrator',
                'email': 'admin@company.com',
                'ad_username': 'admin_ad',
                'dept': depts_dict['IT'],
                'username': 'admin',
                'auth_mode': 'LOCAL',
                'roles': ['Admin', 'Buyer']
            },
            {
                'emp_code': 'EMP002',
                'first_name': 'John',
                'last_name': 'Buyer',
                'email': 'buyer@company.com',
                'ad_username': 'buyer_ad',
                'dept': depts_dict['PROC'],
                'username': 'buyer',
                'auth_mode': 'LOCAL',
                'roles': ['Buyer']
            },
            {
                'emp_code': 'EMP005',
                'first_name': 'David',
                'last_name': 'Auditor',
                'email': 'auditor@company.com',
                'ad_username': 'auditor_ad',
                'dept': depts_dict['FIN'],
                'username': 'auditor',
                'auth_mode': 'LOCAL',
                'roles': ['Auditor']
            },
        ]

        sys_users_dict = {}
        for item in core_users:
            emp, _ = EmployeeMaster.objects.update_or_create(
                employee_code=item['emp_code'],
                defaults={
                    'first_name': item['first_name'],
                    'last_name': item['last_name'],
                    'email': item['email'],
                    'ad_username': item['ad_username'],
                    'department': item['dept'],
                    'is_active': True
                }
            )

            user, _ = SystemUser.objects.update_or_create(
                employee=emp,
                defaults={
                    'username': item['username'],
                    'email': item['email'],
                    'auth_mode': item['auth_mode'],
                    'password_hash': hash_pwd("Password123!"),
                    'is_active': True
                }
            )
            sys_users_dict[item['username']] = user

            for role_code in item['roles']:
                UserRole.objects.get_or_create(
                    user=user,
                    role=roles_dict[role_code]
                )

        # 4. Seed Approver1 through Approver8 in EmployeeMaster & SystemUser
        approver_list = [
            ('EMP003', 'Approver1', 'One', 'approver1@company.com', 'approver1_ad', 'approver1', depts_dict['FIN']),
            ('EMP004', 'Approver2', 'Two', 'approver2@company.com', 'approver2_ad', 'approver2', depts_dict['FIN']),
            ('EMP006', 'Approver3', 'Three', 'approver3@company.com', 'approver3_ad', 'approver3', depts_dict['PROC']),
            ('EMP007', 'Approver4', 'Four', 'approver4@company.com', 'approver4_ad', 'approver4', depts_dict['PROC']),
            ('EMP008', 'Approver5', 'Five', 'approver5@company.com', 'approver5_ad', 'approver5', depts_dict['OPS']),
            ('EMP009', 'Approver6', 'Six', 'approver6@company.com', 'approver6_ad', 'approver6', depts_dict['OPS']),
            ('EMP010', 'Approver7', 'Seven', 'approver7@company.com', 'approver7_ad', 'approver7', depts_dict['IT']),
            ('EMP011', 'Approver8', 'Eight', 'approver8@company.com', 'approver8_ad', 'approver8', depts_dict['HR']),
        ]

        approver_users = []
        for emp_code, f_name, l_name, email, ad_alias, uname, dept in approver_list:
            emp, _ = EmployeeMaster.objects.update_or_create(
                employee_code=emp_code,
                defaults={
                    'first_name': f_name,
                    'last_name': l_name,
                    'email': email,
                    'ad_username': ad_alias,
                    'department': dept,
                    'is_active': True
                }
            )

            user, _ = SystemUser.objects.update_or_create(
                employee=emp,
                defaults={
                    'username': uname,
                    'email': email,
                    'auth_mode': 'LOCAL',
                    'password_hash': hash_pwd("Password123!"),
                    'is_active': True
                }
            )

            UserRole.objects.get_or_create(user=user, role=roles_dict['Approver'])
            approver_users.append(user)

        self.stdout.write("[OK] Seeded admin, buyer, auditor, and approver1..8 with Password123!")

        # 5. Seed Default Admin Department Manual Sequence (Levels 1..8)
        fin_dept = depts_dict['FIN']
        config, _ = DepartmentApproverConfiguration.objects.get_or_create(
            department=fin_dept,
            defaults={'approver_mode': 'MANUAL', 'is_active': True}
        )

        WorkflowConfiguration.objects.get_or_create(
            config=config,
            defaults={'return_mode': 'RETURN_TO_INITIATOR'}
        )

        for idx, app_user in enumerate(approver_users, start=1):
            ManualApproverConfiguration.objects.update_or_create(
                config=config,
                approver_level=idx,
                defaults={'approver_user': app_user, 'is_active': True}
            )

        self.stdout.write("[OK] Seeded 8-Level Manual Approver Sequence (approver1..approver8)")
        self.stdout.write("Database seeding completed successfully!")

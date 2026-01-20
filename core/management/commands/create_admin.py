from django.core.management.base import BaseCommand
from core.models import CustomUser

class Command(BaseCommand):
    help = 'Create a demo admin user'

    def handle(self, *args, **options):
        email = 'admin@mlm.com'
        password = 'Admin@12345'
        
        # Check if admin already exists
        if CustomUser.objects.filter(email=email).exists():
            admin = CustomUser.objects.get(email=email)
            admin.set_password(password)
            admin.is_superuser = True
            admin.is_staff = True
            admin.save()
            self.stdout.write(self.style.WARNING(f'⚠️ Admin user already exists. Password updated.'))
        else:
            # Create new admin
            admin = CustomUser.objects.create_superuser(
                username=email,
                email=email,
                password=password,
                first_name='Admin',
                last_name='User',
                mobile='9999999999',
                sponsor_id='ADMIN001',
                sponsor_name='System Admin',
                is_active_member=True
            )
            self.stdout.write(self.style.SUCCESS(f'✅ Admin user created successfully!'))
        
        self.stdout.write(self.style.SUCCESS('\n=== Admin Login Credentials ==='))
        self.stdout.write(self.style.WARNING(f'Email: {email}'))
        self.stdout.write(self.style.WARNING(f'Password: {password}'))
        self.stdout.write(self.style.SUCCESS(f'\nLogin URL: /admin/login/'))


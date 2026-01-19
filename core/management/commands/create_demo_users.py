from django.core.management.base import BaseCommand
from core.models import CustomUser

class Command(BaseCommand):
    help = 'Create demo users for testing'

    def handle(self, *args, **options):
        # Demo User 1
        if not CustomUser.objects.filter(email='demo@example.com').exists():
            user1 = CustomUser.objects.create_user(
                username='demo@example.com',
                email='demo@example.com',
                password='Demo@12345',
                first_name='Demo',
                last_name='User',
                mobile='9876543210',
                sponsor_id='MLM001',
                sponsor_name='Admin User',
                is_active_member=True
            )
            self.stdout.write(self.style.SUCCESS(f'✅ Created user: demo@example.com'))
        else:
            self.stdout.write(self.style.WARNING('⚠️ User demo@example.com already exists'))

        # Demo User 2
        if not CustomUser.objects.filter(email='user@example.com').exists():
            user2 = CustomUser.objects.create_user(
                username='user@example.com',
                email='user@example.com',
                password='User@12345',
                first_name='John',
                last_name='Doe',
                mobile='9123456789',
                sponsor_id='MLM002',
                sponsor_name='Demo User',
                is_active_member=True
            )
            self.stdout.write(self.style.SUCCESS(f'✅ Created user: user@example.com'))
        else:
            self.stdout.write(self.style.WARNING('⚠️ User user@example.com already exists'))

        # Demo User 3
        if not CustomUser.objects.filter(email='admin@example.com').exists():
            user3 = CustomUser.objects.create_superuser(
                username='admin@example.com',
                email='admin@example.com',
                password='Admin@12345',
                first_name='Admin',
                last_name='User',
                mobile='9000000000',
                sponsor_id='MLM000',
                sponsor_name='System',
                is_active_member=True
            )
            self.stdout.write(self.style.SUCCESS(f'✅ Created superuser: admin@example.com'))
        else:
            self.stdout.write(self.style.WARNING('⚠️ User admin@example.com already exists'))

        self.stdout.write(self.style.SUCCESS('\n=== Demo Users Created Successfully ==='))
        self.stdout.write(self.style.WARNING('\nLogin Credentials:\n'))
        self.stdout.write('1️⃣  Email: demo@example.com\n   Password: Demo@12345\n')
        self.stdout.write('2️⃣  Email: user@example.com\n   Password: User@12345\n')
        self.stdout.write('3️⃣  Email: admin@example.com\n   Password: Admin@12345 (Superuser)\n')

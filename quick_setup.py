#!/usr/bin/env python
"""
Quick setup script to create superuser and test data
Run with: .venv\Scripts\activate && python quick_setup.py
"""

import os
import django
import sys

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from django.contrib.auth import get_user_model
from users.models import AadhaarRecord, PANRecord

def create_superuser():
    """Create superuser for admin access"""
    User = get_user_model()
    
    username = 'admin'
    email = 'admin@neobank.com'
    password = 'admin123'
    
    if User.objects.filter(username=username).exists():
        print(f"✅ Superuser '{username}' already exists!")
        return True
    
    try:
        user = User.objects.create_superuser(
            username=username,
            email=email,
            password=password
        )
        print(f"🎉 Superuser created successfully!")
        print(f"   Username: {username}")
        print(f"   Email: {email}")
        print(f"   Password: {password}")
        return True
        
    except Exception as e:
        print(f"❌ Error creating superuser: {e}")
        return False

def create_test_aadhaar():
    """Create one test Aadhaar record"""
    aadhaar_number = '123456789012'
    aadhaar_hash = AadhaarRecord.generate_hash(aadhaar_number)
    
    if AadhaarRecord.objects.filter(aadhaar_hash=aadhaar_hash).exists():
        print(f"✅ Test Aadhaar already exists (****9012)")
        return True
    
    try:
        from datetime import datetime
        record = AadhaarRecord.objects.create(
            aadhaar_last_4='9012',
            aadhaar_hash=aadhaar_hash,
            full_name='John Doe',
            date_of_birth=datetime.strptime('1990-01-15', '%Y-%m-%d').date(),
            gender='M',
            address_line='123 Sample Street, Test City, Test State',
            pin_code='400001',
            is_active=True,
            created_by='setup_script'
        )
        print(f"✅ Created test Aadhaar: John Doe (****9012)")
        return True
        
    except Exception as e:
        print(f"❌ Error creating test Aadhaar: {e}")
        return False

def main():
    print("🚀 Quick NeoBank Setup")
    print("=" * 30)
    
    # Create superuser
    superuser_ok = create_superuser()
    
    # Create test data
    test_data_ok = create_test_aadhaar()
    
    if superuser_ok:
        print("\n🎯 READY TO USE!")
        print("=" * 30)
        print(f"Admin: http://127.0.0.1:8000/admin/")
        print(f"Login: admin / admin123")
        print(f"Signup: http://127.0.0.1:8000/users/signup/")
        print(f"Test Aadhaar: 123456789012")
        print(f"Test Name: John Doe")
        print(f"Test DOB: 1990-01-15")
        print(f"Test Gender: Male")
        print("\n🏃‍♂️ Run: python manage.py runserver")

if __name__ == '__main__':
    main()

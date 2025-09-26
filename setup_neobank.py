#!/usr/bin/env python
"""
Complete setup script for NeoBank project
This will:
1. Create superuser
2. Add sample Aadhaar and PAN records for testing
3. Show you how to test the system
"""

import os
import django
import sys
from datetime import datetime

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
        return User.objects.get(username=username)
    
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
        return user
        
    except Exception as e:
        print(f"❌ Error creating superuser: {e}")
        return None

def create_sample_aadhaar_records():
    """Create sample Aadhaar records for testing"""
    print("\n📝 Creating sample Aadhaar records...")
    
    sample_aadhaars = [
        {
            'number': '123456789012',
            'name': 'John Doe',
            'dob': '1990-01-15',
            'gender': 'M',
            'address': '123 Sample Street, Test City, Test State',
            'pin': '400001'
        },
        {
            'number': '987654321098',
            'name': 'Jane Smith',
            'dob': '1985-05-20',
            'gender': 'F',
            'address': '456 Example Road, Demo City, Demo State',
            'pin': '110001'
        },
        {
            'number': '555666777888',
            'name': 'Bob Johnson',
            'dob': '1992-08-10',
            'gender': 'M',
            'address': '789 Test Avenue, Sample City, Sample State',
            'pin': '600001'
        }
    ]
    
    created_count = 0
    for aadhaar_data in sample_aadhaars:
        aadhaar_hash = AadhaarRecord.generate_hash(aadhaar_data['number'])
        
        # Check if already exists
        if AadhaarRecord.objects.filter(aadhaar_hash=aadhaar_hash).exists():
            print(f"   ⚠️  Aadhaar ending in {aadhaar_data['number'][-4:]} already exists")
            continue
        
        try:
            record = AadhaarRecord.objects.create(
                aadhaar_last_4=aadhaar_data['number'][-4:],
                aadhaar_hash=aadhaar_hash,
                full_name=aadhaar_data['name'],
                date_of_birth=datetime.strptime(aadhaar_data['dob'], '%Y-%m-%d').date(),
                gender=aadhaar_data['gender'],
                address_line=aadhaar_data['address'],
                pin_code=aadhaar_data['pin'],
                is_active=True,
                created_by='setup_script'
            )
            print(f"   ✅ Created Aadhaar record for {aadhaar_data['name']} (****{aadhaar_data['number'][-4:]})")
            created_count += 1
            
        except Exception as e:
            print(f"   ❌ Error creating Aadhaar for {aadhaar_data['name']}: {e}")
    
    print(f"📊 Created {created_count} new Aadhaar records")
    return created_count

def create_sample_pan_records():
    """Create sample PAN records for testing"""
    print("\n📝 Creating sample PAN records...")
    
    sample_pans = [
        {
            'number': 'ABCDE1234F',
            'name': 'John Doe',
            'dob': '1990-01-15',
            'father': 'Richard Doe'
        },
        {
            'number': 'PQRST5678G',
            'name': 'Jane Smith',
            'dob': '1985-05-20',
            'father': 'Michael Smith'
        },
        {
            'number': 'XYZ123456H',
            'name': 'Bob Johnson',
            'dob': '1992-08-10',
            'father': 'William Johnson'
        }
    ]
    
    created_count = 0
    for pan_data in sample_pans:
        pan_hash = PANRecord.generate_hash(pan_data['number'])
        
        # Check if already exists
        if PANRecord.objects.filter(pan_hash=pan_hash).exists():
            print(f"   ⚠️  PAN ending in {pan_data['number'][-4:]} already exists")
            continue
        
        try:
            record = PANRecord.objects.create(
                pan_last_4=pan_data['number'][-4:],
                pan_hash=pan_hash,
                full_name=pan_data['name'],
                date_of_birth=datetime.strptime(pan_data['dob'], '%Y-%m-%d').date(),
                father_name=pan_data['father'],
                pan_status='active',
                is_active=True,
                created_by='setup_script'
            )
            print(f"   ✅ Created PAN record for {pan_data['name']} (***{pan_data['number'][-4:]})")
            created_count += 1
            
        except Exception as e:
            print(f"   ❌ Error creating PAN for {pan_data['name']}: {e}")
    
    print(f"📊 Created {created_count} new PAN records")
    return created_count

def show_test_instructions():
    """Show testing instructions"""
    print("\n" + "="*60)
    print("🎉 NEOBANK SETUP COMPLETE!")
    print("="*60)
    
    print("\n📋 ADMIN ACCESS:")
    print("   URL: http://127.0.0.1:8000/admin/")
    print("   Username: admin")
    print("   Password: admin123")
    
    print("\n📋 SIGNUP TESTING:")
    print("   URL: http://127.0.0.1:8000/users/signup/")
    
    print("\n📋 TEST AADHAAR NUMBERS:")
    print("   123456789012 - John Doe (DOB: 1990-01-15, Gender: M)")
    print("   987654321098 - Jane Smith (DOB: 1985-05-20, Gender: F)")
    print("   555666777888 - Bob Johnson (DOB: 1992-08-10, Gender: M)")
    
    print("\n📋 TEST PAN NUMBERS:")
    print("   ABCDE1234F - John Doe")
    print("   PQRST5678G - Jane Smith")
    print("   XYZ123456H - Bob Johnson")
    
    print("\n📋 TESTING STEPS:")
    print("   1. Start server: python manage.py runserver")
    print("   2. Go to signup: http://127.0.0.1:8000/users/signup/")
    print("   3. Complete Steps 1-2 (Mobile OTP + Personal Details)")
    print("   4. In Step 3, use one of the test Aadhaar numbers above")
    print("   5. Make sure name and DOB match exactly!")
    print("   6. Check console for OTP when prompted")
    
    print("\n📋 ADMIN MANAGEMENT:")
    print("   • Go to Admin → Aadhaar Records to add more test data")
    print("   • Use the 'Full Aadhaar Number' field to input complete numbers")
    print("   • System will automatically hash and secure the data")
    
    print("\n⚠️  IMPORTANT NOTES:")
    print("   • Personal details (name, DOB, gender) must EXACTLY match")
    print("   • OTP will appear in the console (demo mode)")
    print("   • Only pre-approved Aadhaar numbers will work")
    
    print("\n🚀 Ready to test! Run: python manage.py runserver")
    print("="*60)

def main():
    print("🏦 NeoBank Setup Script")
    print("="*40)
    
    # Create superuser
    user = create_superuser()
    if not user:
        print("❌ Failed to create superuser. Exiting...")
        return
    
    # Create sample data
    aadhaar_count = create_sample_aadhaar_records()
    pan_count = create_sample_pan_records()
    
    # Show instructions
    show_test_instructions()

if __name__ == '__main__':
    main()

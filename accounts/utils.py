import random
import string
from datetime import datetime, timedelta
from django.utils import timezone
from django.core.exceptions import ValidationError


def generate_otp(length=6):
    """Generate a random OTP of specified length"""
    return ''.join([str(random.randint(0, 9)) for _ in range(length)])


def send_otp_sms(phone, otp, otp_type="verification"):
    """Mock SMS sending function - outputs to console for development"""
    print(f"\n{'='*50}")
    print(f"📱 SMS SENT ({otp_type.upper()})")
    print(f"📞 To: {phone}")
    print(f"🔢 OTP: {otp}")
    print(f"⏰ Time: {timezone.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'='*50}\n")
    
    # In production, integrate with SMS provider like:
    # - Twilio
    # - AWS SNS
    # - TextLocal
    # - MSG91
    return True


def verify_aadhaar(aadhaar_number, full_name):
    """Mock Aadhaar verification - simulates UIDAI verification"""
    # In production, integrate with UIDAI's e-KYC API
    # For demo purposes, we'll simulate verification
    
    # Mock verification logic
    if len(aadhaar_number) != 12 or not aadhaar_number.isdigit():
        return {
            'success': False,
            'message': 'Invalid Aadhaar number format'
        }
    
    # Simulate verification success
    return {
        'success': True,
        'message': 'Aadhaar verification successful',
        'name_on_aadhaar': full_name,  # In real implementation, this comes from UIDAI
        'masked_aadhaar': mask_aadhaar(aadhaar_number)
    }


def verify_pan(pan_number, full_name):
    """Mock PAN verification - simulates IT Department verification"""
    # In production, integrate with IT Department's PAN verification API
    # For demo purposes, we'll simulate verification
    
    # Mock verification logic
    if len(pan_number) != 10:
        return {
            'success': False,
            'message': 'Invalid PAN number format'
        }
    
    # Simulate verification success
    return {
        'success': True,
        'message': 'PAN verification successful',
        'name_on_pan': full_name,  # In real implementation, this comes from IT Department
        'masked_pan': mask_pan(pan_number)
    }


def generate_account_number():
    """Generate a unique account number"""
    # In production, use a more sophisticated algorithm
    # For demo purposes, generate a 10-digit number
    return random.randint(1000000000, 9999999999)


def generate_customer_id():
    """Generate a unique 5-digit customer ID (10000-99999)"""
    from .models import CustomUser
    
    max_attempts = 1000  # Prevent infinite loop
    attempts = 0
    
    while attempts < max_attempts:
        customer_id = random.randint(10000, 99999)
        # Check if it already exists
        if not CustomUser.objects.filter(customer_id=customer_id).exists():
            return customer_id
        attempts += 1
    
    # Fallback: if all IDs are taken (unlikely but handle it)
    raise ValueError("Unable to generate unique customer ID. Please contact support.")


def mask_aadhaar(aadhaar_number):
    """Mask Aadhaar number for display (show first 4 and last 4 digits)"""
    if len(aadhaar_number) != 12:
        return "XXXX-XXXX-****"
    
    return f"{aadhaar_number[:4]}-{aadhaar_number[4:8]}-****"


def mask_pan(pan_number):
    """Mask PAN number for display (show first 5 characters)"""
    if len(pan_number) != 10:
        return "XXXXX****"
    
    return f"{pan_number[:5]}****"


def calculate_credit_score(user_data):
    """Calculate a mock credit score based on user data"""
    # In production, integrate with credit bureaus like:
    # - CIBIL
    # - Experian
    # - Equifax
    # - CRIF High Mark
    
    base_score = 500
    
    # Mock scoring factors
    age = (timezone.now().date() - user_data.get('date_of_birth', timezone.now().date())).days // 365
    
    if age >= 25:
        base_score += 50
    
    # Add some randomness for demo
    base_score += random.randint(-50, 100)
    
    # Ensure score is within valid range
    return max(300, min(900, base_score))


def generate_username(full_name, phone):
    """Generate a unique username from full name and phone"""
    # Create username from name initials + last 4 digits of phone
    name_parts = full_name.lower().split()
    initials = ''.join([part[0] for part in name_parts[:2]])  # First 2 initials
    phone_suffix = phone[-4:]  # Last 4 digits
    
    username = f"{initials}{phone_suffix}"
    
    # Add random suffix if needed for uniqueness
    from .models import CustomUser
    if CustomUser.objects.filter(username=username).exists():
        username += str(random.randint(10, 99))
    
    return username


def format_phone_number(phone, country_code='+91'):
    """Format phone number for display"""
    if len(phone) == 10:
        return f"{country_code} {phone[:5]} {phone[5:]}"
    return f"{country_code} {phone}"


def get_expiry_time(minutes=30):
    """Get expiry time for signup sessions (default: 30 minutes)"""
    return timezone.now() + timedelta(minutes=minutes)


def is_signup_expired(expires_at):
    """Check if signup session has expired"""
    return timezone.now() > expires_at


def clean_expired_signups():
    """Clean up expired signup progress records"""
    from .models import SignupProgress
    
    expired_count = SignupProgress.objects.filter(
        expires_at__lt=timezone.now()
    ).delete()[0]
    
    return expired_count


def validate_aadhaar_checksum(aadhaar_number):
    """Validate Aadhaar number using Verhoeff algorithm (simplified)"""
    # This is a simplified version. In production, use the full Verhoeff algorithm
    if len(aadhaar_number) != 12:
        return False
    
    # Basic validation - not a real checksum
    return aadhaar_number.isdigit()


def validate_pan_format(pan_number):
    """Validate PAN number format"""
    import re
    
    # PAN format: 5 letters + 4 digits + 1 letter
    pattern = r'^[A-Z]{5}[0-9]{4}[A-Z]$'
    return bool(re.match(pattern, pan_number))


def get_step_name(step_number):
    """Get human-readable step name"""
    step_names = {
        1: "Mobile Verification",
        2: "Personal Details", 
        3: "Aadhaar Verification",
        4: "PAN Verification",
        5: "PIN Setup"
    }
    return step_names.get(step_number, "Unknown Step")


def get_next_step_url(step_number):
    """Get URL for next step"""
    step_urls = {
        1: "accounts:signup_step2",
        2: "accounts:signup_step3",
        3: "accounts:signup_step4", 
        4: "accounts:signup_step5",
        5: "accounts:signup_success"
    }
    return step_urls.get(step_number)


def get_previous_step_url(step_number):
    """Get URL for previous step"""
    step_urls = {
        2: "accounts:signup_step1",
        3: "accounts:signup_step2",
        4: "accounts:signup_step3",
        5: "accounts:signup_step4"
    }
    return step_urls.get(step_number)

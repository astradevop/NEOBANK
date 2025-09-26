# users/models.py
"""
Beginner-friendly models for the NeoBank signup flow.

This file defines:
- CustomUser: a user record that extends Django's built-in user to hold phone and KYC fields.
- SignupSession: stores the temporary state for the 5-step signup (OTP, step data, expiry).
- KYCRecord: stores KYC provider responses and status per signup session.
- Account: very small placeholder to show account details after signup completes.

Read the inline comments — they explain why each field exists.
"""

import uuid
from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils import timezone


# -----------------------
# 1) CustomUser
# -----------------------
class CustomUser(AbstractUser):
    """
    Extend Django's AbstractUser for easy first-time use.
    AbstractUser already provides username/password/first_name/last_name/email.
    We add phone and a few KYC-related fields.

    NOTE:
    - For a production phone-as-username system you'd set USERNAME_FIELD = 'phone'
      and remove username; that requires updating auth flows and admin. We'll keep it
      simple for learning.
    """
    phone = models.CharField(
        max_length=20,
        unique=True,
        null=True,
        blank=True,
        help_text="User's primary mobile number (store E.164 or digits-only)."
    )
    is_phone_verified = models.BooleanField(default=False)

    # Simple KYC fields (store masked values only for privacy)
    pan_masked = models.CharField(max_length=20, null=True, blank=True)
    aadhaar_masked = models.CharField(max_length=20, null=True, blank=True)
    
    # PIN/Passcode fields for secure login
    pin_hash = models.CharField(
        max_length=128, 
        null=True, 
        blank=True,
        help_text="Hashed 6-digit PIN for secure login (never store plain PIN)"
    )
    pin_set_at = models.DateTimeField(
        null=True, 
        blank=True,
        help_text="When the PIN was last set or updated"
    )
    pin_attempts = models.IntegerField(
        default=0,
        help_text="Number of failed PIN attempts (for security)"
    )
    pin_locked_until = models.DateTimeField(
        null=True, 
        blank=True,
        help_text="PIN locked until this time (if too many failed attempts)"
    )

    # A convenience method to show masked PAN (example: XXXXT1234)
    def get_pan_masked(self):
        return self.pan_masked or ""

    def set_pin(self, pin):
        """
        Set a new 6-digit PIN for the user.
        - pin: 6-digit string like '123456'
        - Automatically hashes the PIN for secure storage
        - Updates pin_set_at timestamp
        - Resets failed attempt counters
        """
        import hashlib
        from django.utils import timezone
        
        # Validate PIN format
        if not pin or len(pin) != 6 or not pin.isdigit():
            raise ValueError("PIN must be exactly 6 digits")
        
        # Hash the PIN using SHA-256 (in production, use bcrypt or similar)
        pin_hash = hashlib.sha256(pin.encode()).hexdigest()
        
        # Update user fields
        self.pin_hash = pin_hash
        self.pin_set_at = timezone.now()
        self.pin_attempts = 0
        self.pin_locked_until = None
        self.save(update_fields=['pin_hash', 'pin_set_at', 'pin_attempts', 'pin_locked_until'])
    
    def verify_pin(self, pin):
        """
        Verify a PIN against the stored hash.
        - pin: 6-digit string to verify
        - Returns (True, None) on success
        - Returns (False, reason) on failure: 'locked', 'wrong', 'no_pin'
        """
        from django.utils import timezone
        import hashlib
        
        # Check if PIN is locked
        if self.pin_locked_until and timezone.now() < self.pin_locked_until:
            return False, 'locked'
        
        # Check if PIN is set
        if not self.pin_hash:
            return False, 'no_pin'
        
        # Validate PIN format
        if not pin or len(pin) != 6 or not pin.isdigit():
            return False, 'invalid_format'
        
        # Hash the provided PIN and compare
        pin_hash = hashlib.sha256(pin.encode()).hexdigest()
        
        if pin_hash == self.pin_hash:
            # Success - reset failed attempts
            self.pin_attempts = 0
            self.pin_locked_until = None
            self.save(update_fields=['pin_attempts', 'pin_locked_until'])
            return True, None
        else:
            # Failed attempt - increment counter
            self.pin_attempts += 1
            
            # Lock PIN after 3 failed attempts for 15 minutes
            if self.pin_attempts >= 3:
                self.pin_locked_until = timezone.now() + timezone.timedelta(minutes=15)
            
            self.save(update_fields=['pin_attempts', 'pin_locked_until'])
            return False, 'wrong'
    
    def is_pin_locked(self):
        """Check if PIN is currently locked due to failed attempts."""
        from django.utils import timezone
        return self.pin_locked_until and timezone.now() < self.pin_locked_until
    
    def get_pin_lock_time_remaining(self):
        """Get remaining lock time in minutes (0 if not locked)."""
        from django.utils import timezone
        if not self.is_pin_locked():
            return 0
        remaining = self.pin_locked_until - timezone.now()
        return max(0, int(remaining.total_seconds() / 60))

    def __str__(self):
        # Useful string in admin and shell
        if self.phone:
            return f"{self.username or self.email or 'user'} — {self.phone}"
        return self.username or self.email or str(self.pk)


# -----------------------
# 2) SignupSession
# -----------------------
class SignupSession(models.Model):
    """
    This model holds ephemeral data while a user completes the multi-step signup.
    - session_id: unique identifier that the frontend will keep and pass to backend.
    - phone: phone number the session is for (helps searching).
    - current_step: integer 1..5 tracking which step the user is on.
    - data: JSON to stash step payloads (personal details, aadhaar partial, etc).
    - otp_code: simple column for demo. In real systems store OTP hashed in Redis.
    - otp_expires_at: when the OTP will no longer be valid.
    - is_completed: True after final step is done and user/account created.
    """

    session_id = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    phone = models.CharField(max_length=20, db_index=True)
    current_step = models.IntegerField(default=1)
    data = models.JSONField(default=dict, blank=True)  # store partial step payloads here
    is_completed = models.BooleanField(default=False)

    # Simple OTP storage for learning/demo:
    # - In production: do NOT store plain OTPs in the database. Use Redis + hash.
    otp_code = models.CharField(max_length=10, null=True, blank=True,
                                help_text="For demo only. Store hashed OTP in real apps.")
    otp_expires_at = models.DateTimeField(null=True, blank=True)

    otp_attempts = models.IntegerField(default=0,
                                       help_text="Increment on each wrong OTP attempt for throttling.")

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    # Convenience helpers:
    def otp_is_valid(self):
        """Return True if OTP is set and not expired."""
        if not self.otp_code or not self.otp_expires_at:
            return False
        return timezone.now() <= self.otp_expires_at

    def set_otp(self, code, ttl_seconds=300):
        """
        Set an OTP and expiry. (Demo only.)
        - code: string like '123456'
        - ttl_seconds: how long the OTP lives
        """
        self.otp_code = str(code)
        self.otp_expires_at = timezone.now() + timezone.timedelta(seconds=ttl_seconds)
        self.otp_attempts = 0
        self.save(update_fields=['otp_code', 'otp_expires_at', 'otp_attempts', 'updated_at'])

    def verify_otp(self, code):
        """
        Verify the provided code:
        - Returns (True, None) on success.
        - Returns (False, reason) on failure: 'expired' or 'wrong' or 'no_otp'.
        """
        if not self.otp_code:
            return False, 'no_otp'
        if not self.otp_is_valid():
            return False, 'expired'
        if str(code) == self.otp_code:
            # consume OTP (demo)
            self.otp_code = None
            self.otp_expires_at = None
            self.otp_attempts = 0
            self.current_step = max(self.current_step, 2)  # move to step 2 after OTP
            self.save(update_fields=['otp_code', 'otp_expires_at', 'otp_attempts', 'current_step', 'updated_at'])
            return True, None
        else:
            self.otp_attempts += 1
            self.save(update_fields=['otp_attempts', 'updated_at'])
            return False, 'wrong'

    def __str__(self):
        return f"SignupSession {self.session_id} — phone={self.phone} step={self.current_step}"


# -----------------------
# 3) KYCRecord
# -----------------------
class KYCRecord(models.Model):
    """
    Store KYC verification attempts/results.
    Examples:
      - provider='aadhaar' response={'status': 'success', ...}
      - provider='pan' response={'status': 'mismatch', ...}
    """
    PROVIDER_CHOICES = [
        ('aadhaar', 'Aadhaar'),
        ('pan', 'PAN'),
        ('cibil', 'CIBIL'),
    ]

    session = models.ForeignKey(SignupSession, on_delete=models.CASCADE, related_name='kyc_records')
    provider = models.CharField(max_length=30, choices=PROVIDER_CHOICES)
    status = models.CharField(max_length=30, help_text="eg: pending, success, failed")
    response = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"KYC {self.provider} for session {self.session.session_id} => {self.status}"


# -----------------------
# 4) Account (simple)
# -----------------------
class Account(models.Model):
    """
    A simple account model to show the successState details in your template.
    - In production you'd have ledger tables, balances, account types, etc.
    """
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='accounts')
    account_number = models.CharField(max_length=32, unique=True)
    display_name = models.CharField(max_length=100, blank=True, help_text="eg: NeoBank Savings")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.account_number} ({self.user.phone or self.user.username})"


# -----------------------
# 5) Simple utility functions (optional helpers)
# -----------------------
def mask_pan(pan: str) -> str:
    """
    Mask PAN keeping last 4 characters, e.g. 'ABCDE1234F' -> 'XXXXX1234F'
    Use this before saving to CustomUser.pan_masked.
    """
    if not pan or len(pan) < 4:
        return pan
    return 'X' * max(0, len(pan) - 4) + pan[-4:]


def mask_aadhaar(aadhaar: str) -> str:
    """
    Mask Aadhaar keeping last 4 digits: '123412341234' -> 'XXXXXXXX1234'
    """
    digits = ''.join(c for c in (aadhaar or "") if c.isdigit())
    if len(digits) <= 4:
        return digits
    return 'X' * (len(digits) - 4) + digits[-4:]


# -----------------------
# 6) AadhaarRecord - Admin managed Aadhaar data
# -----------------------
class AadhaarRecord(models.Model):
    """
    Admin-managed Aadhaar records that are pre-approved for verification.
    
    Why this exists:
    - In a real system, you'd integrate with UIDAI (Unique Identification Authority of India)
    - For this demo, admin can pre-populate approved Aadhaar numbers
    - Only these numbers will pass verification
    - Stores minimal required data for KYC compliance
    
    Security Notes:
    - Never store full Aadhaar numbers in production
    - This is a simplified demo model
    - In production, use encrypted storage and hashed references
    """
    
    # Store only last 4 digits + a hash reference for lookup
    aadhaar_last_4 = models.CharField(
        max_length=4, 
        db_index=True,
        help_text="Last 4 digits of Aadhaar for display purposes"
    )
    
    # Hash of full Aadhaar for verification (in production, use proper hashing)
    aadhaar_hash = models.CharField(
        max_length=64, 
        unique=True,
        help_text="Hash of full Aadhaar number for verification"
    )
    
    # Basic details that would come from UIDAI verification
    full_name = models.CharField(
        max_length=100,
        help_text="Name as per Aadhaar"
    )
    
    date_of_birth = models.DateField(
        help_text="DOB as per Aadhaar (YYYY-MM-DD)"
    )
    
    gender = models.CharField(
        max_length=1,
        choices=[('M', 'Male'), ('F', 'Female'), ('O', 'Other')],
        help_text="Gender as per Aadhaar"
    )
    
    # Address information (simplified)
    address_line = models.TextField(
        help_text="Address as per Aadhaar"
    )
    
    pin_code = models.CharField(
        max_length=6,
        help_text="PIN code as per Aadhaar"
    )
    
    # Admin metadata
    is_active = models.BooleanField(
        default=True,
        help_text="Set to False to disable this Aadhaar record"
    )
    
    created_by = models.CharField(
        max_length=50,
        default='admin',
        help_text="Admin user who created this record"
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Aadhaar Record"
        verbose_name_plural = "Aadhaar Records"
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.full_name} (****{self.aadhaar_last_4})"
    
    def get_masked_aadhaar(self):
        """Return masked Aadhaar for display"""
        return f"XXXX-XXXX-{self.aadhaar_last_4}"
    
    @staticmethod
    def generate_hash(aadhaar_number):
        """Generate hash for Aadhaar number (simplified for demo)"""
        import hashlib
        return hashlib.sha256(aadhaar_number.encode()).hexdigest()


# -----------------------
# 7) PANRecord - Admin managed PAN data
# -----------------------
class PANRecord(models.Model):
    """
    Admin-managed PAN records that are pre-approved for verification.
    
    Similar to AadhaarRecord, this allows admin to pre-populate valid PAN numbers
    that will pass KYC verification. In production, you'd integrate with
    Income Tax Department APIs or authorized PAN verification services.
    """
    
    # Store last 4 characters for display (format: ABCDE1234F -> 1234F)
    pan_last_4 = models.CharField(
        max_length=5, 
        db_index=True,
        help_text="Last 4 characters of PAN for display"
    )
    
    # Hash of full PAN for verification
    pan_hash = models.CharField(
        max_length=64, 
        unique=True,
        help_text="Hash of full PAN for verification"
    )
    
    # PAN holder details
    full_name = models.CharField(
        max_length=100,
        help_text="Name as per PAN"
    )
    
    date_of_birth = models.DateField(
        help_text="DOB as per PAN (YYYY-MM-DD)"
    )
    
    father_name = models.CharField(
        max_length=100,
        blank=True,
        help_text="Father's name as per PAN"
    )
    
    # PAN status
    pan_status = models.CharField(
        max_length=20,
        choices=[
            ('active', 'Active'),
            ('inactive', 'Inactive'),
            ('cancelled', 'Cancelled'),
        ],
        default='active',
        help_text="PAN status as per IT Department"
    )
    
    # Admin metadata
    is_active = models.BooleanField(
        default=True,
        help_text="Set to False to disable this PAN record"
    )
    
    created_by = models.CharField(
        max_length=50,
        default='admin',
        help_text="Admin user who created this record"
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "PAN Record"
        verbose_name_plural = "PAN Records"
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.full_name} (***{self.pan_last_4})"
    
    def get_masked_pan(self):
        """Return masked PAN for display"""
        return f"XXXXX{self.pan_last_4}"
    
    @staticmethod
    def generate_hash(pan_number):
        """Generate hash for PAN number (simplified for demo)"""
        import hashlib
        return hashlib.sha256(pan_number.upper().encode()).hexdigest()
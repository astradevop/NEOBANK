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

    # A convenience method to show masked PAN (example: XXXXT1234)
    def get_pan_masked(self):
        return self.pan_masked or ""

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

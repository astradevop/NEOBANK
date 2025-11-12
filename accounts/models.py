from django.db import models
from django.contrib.auth.models import AbstractUser
from django.core.validators import RegexValidator


class CustomUser(AbstractUser):
    mobile = models.CharField(
        max_length=10,
        unique=True
    )
    email = models.EmailField(unique=True)
    customer_id = models.IntegerField(unique=True, null=True, blank=True, editable=False, help_text="5-digit unique customer identifier")
    full_name = models.CharField(max_length=30)
    date_of_birth = models.DateField()
    gender = models.CharField(max_length=1, choices=[('M', 'Male'), ('F', 'Female'), ('O', 'Other')])
    aadhaar_number = models.CharField(max_length=12, unique=True)
    pan_number = models.CharField(max_length=10, unique=True)
    current_address = models.TextField()
    pin = models.IntegerField()
    ACCOUNT_STATUS_CHOICES = [
        ('pending', 'Pending Approval'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('frozen', 'Frozen'),
    ]
    account_status = models.CharField(max_length=20, choices=ACCOUNT_STATUS_CHOICES, default='pending')
    credit_score = models.IntegerField(default=500, help_text="Credit score for pre-approvals")
    terms_accepted_at = models.DateTimeField(null=True, blank=True)
    account_approved_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    approved_by = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True,
                                    related_name='approved_accounts')
    rejection_reason = models.TextField(blank=True)

    groups = models.ManyToManyField(
        'auth.Group',
        verbose_name='groups',
        blank=True,
        help_text='The groups this user belongs to.',
        related_name="customuser_set",
        related_query_name="customuser",
    )
    user_permissions = models.ManyToManyField(
        'auth.Permission',
        verbose_name='user permissions',
        blank=True,
        help_text='Specific permissions for this user.',
        related_name="customuser_set",
        related_query_name="customuser",
    )

    USERNAME_FIELD = 'mobile'
    REQUIRED_FIELDS = ['email', 'full_name', 'date_of_birth', 'gender', 'aadhaar_number', 'pan_number',
                       'current_address', 'pin']

    class Meta:
        db_table = 'custom_user'


class Account(models.Model):
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE, related_name='account')
    account_number = models.BigIntegerField(unique=True)
    balance = models.DecimalField(max_digits=15, decimal_places=2, default=0.00)
    account_type = models.CharField(max_length=20, default='savings')
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'account'


class SignupProgress(models.Model):
    session_id = models.CharField(max_length=100, unique=True)
    current_step = models.IntegerField(default=1)
    
    # Step 1: Mobile verification
    phone = models.CharField(max_length=15, blank=True)
    country_code = models.CharField(max_length=5, default='+91')
    mobile_otp = models.CharField(max_length=6, blank=True)
    mobile_verified = models.BooleanField(default=False)
    mobile_verified_at = models.DateTimeField(null=True, blank=True)
    
    # Step 2: Personal details
    full_name = models.CharField(max_length=100, blank=True)
    email = models.EmailField(blank=True)
    date_of_birth = models.DateField(null=True, blank=True)
    gender = models.CharField(max_length=1, choices=[('M', 'Male'), ('F', 'Female'), ('O', 'Other')], blank=True)
    
    # Step 3: Aadhaar verification
    aadhaar_number = models.CharField(max_length=12, blank=True)
    current_address = models.TextField(blank=True)
    aadhaar_otp = models.CharField(max_length=6, blank=True)
    aadhaar_verified = models.BooleanField(default=False)
    aadhaar_verified_at = models.DateTimeField(null=True, blank=True)
    aadhaar_name = models.CharField(max_length=100, blank=True)
    
    # Step 4: PAN verification
    pan_number = models.CharField(max_length=10, blank=True)
    pan_otp = models.CharField(max_length=6, blank=True)
    pan_verified = models.BooleanField(default=False)
    pan_verified_at = models.DateTimeField(null=True, blank=True)
    pan_name = models.CharField(max_length=100, blank=True)
    
    # Step 5: PIN setup
    pin = models.CharField(max_length=6, blank=True)
    terms_accepted = models.BooleanField(default=False)
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    expires_at = models.DateTimeField()
    
    class Meta:
        db_table = 'signup_progress'
        ordering = ['-created_at']
from django.contrib import admin
from django import forms
from .models import CustomUser, SignupSession, KYCRecord, Account, AadhaarRecord, PANRecord


# ==========================================
# CUSTOM FORMS FOR ADMIN
# ==========================================

class AadhaarRecordForm(forms.ModelForm):
    """
    Custom form for AadhaarRecord admin to allow inputting full Aadhaar number
    """
    full_aadhaar_number = forms.CharField(
        max_length=12,
        min_length=12,
        required=True,
        help_text="Enter the complete 12-digit Aadhaar number. It will be hashed for security.",
        widget=forms.TextInput(attrs={
            'placeholder': '123456789012',
            'pattern': '[0-9]{12}',
            'title': 'Please enter exactly 12 digits'
        })
    )
    
    class Meta:
        model = AadhaarRecord
        fields = ['full_aadhaar_number', 'full_name', 'date_of_birth', 'gender', 
                 'address_line', 'pin_code', 'is_active']
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Hide the hash and last_4 fields since they're auto-generated
        if 'aadhaar_hash' in self.fields:
            del self.fields['aadhaar_hash']
        if 'aadhaar_last_4' in self.fields:
            del self.fields['aadhaar_last_4']
    
    def clean_full_aadhaar_number(self):
        """Validate Aadhaar number format"""
        aadhaar = self.cleaned_data.get('full_aadhaar_number')
        
        if not aadhaar:
            raise forms.ValidationError("Aadhaar number is required")
        
        # Remove any spaces or special characters
        aadhaar_digits = ''.join(filter(str.isdigit, aadhaar))
        
        if len(aadhaar_digits) != 12:
            raise forms.ValidationError("Aadhaar number must be exactly 12 digits")
        
        # Check if this Aadhaar already exists
        aadhaar_hash = AadhaarRecord.generate_hash(aadhaar_digits)
        existing = AadhaarRecord.objects.filter(aadhaar_hash=aadhaar_hash)
        
        # Exclude current instance if editing
        if self.instance.pk:
            existing = existing.exclude(pk=self.instance.pk)
        
        if existing.exists():
            raise forms.ValidationError("This Aadhaar number is already registered")
        
        return aadhaar_digits
    
    def save(self, commit=True):
        """Override save to generate hash and last_4 from full number"""
        instance = super().save(commit=False)
        
        full_aadhaar = self.cleaned_data.get('full_aadhaar_number')
        if full_aadhaar:
            instance.aadhaar_hash = AadhaarRecord.generate_hash(full_aadhaar)
            instance.aadhaar_last_4 = full_aadhaar[-4:]
        
        if commit:
            instance.save()
        return instance


class PANRecordForm(forms.ModelForm):
    """
    Custom form for PANRecord admin to allow inputting full PAN number
    """
    full_pan_number = forms.CharField(
        max_length=10,
        min_length=10,
        required=True,
        help_text="Enter the complete PAN number (format: ABCDE1234F). It will be hashed for security.",
        widget=forms.TextInput(attrs={
            'placeholder': 'ABCDE1234F',
            'style': 'text-transform: uppercase;',
            'pattern': '[A-Z]{5}[0-9]{4}[A-Z]{1}',
            'title': 'Please enter PAN in format: 5 letters, 4 digits, 1 letter'
        })
    )
    
    class Meta:
        model = PANRecord
        fields = ['full_pan_number', 'full_name', 'date_of_birth', 'father_name', 
                 'pan_status', 'is_active']
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Hide the hash and last_4 fields since they're auto-generated
        if 'pan_hash' in self.fields:
            del self.fields['pan_hash']
        if 'pan_last_4' in self.fields:
            del self.fields['pan_last_4']
    
    def clean_full_pan_number(self):
        """Validate PAN number format"""
        pan = self.cleaned_data.get('full_pan_number', '').upper()
        
        if not pan:
            raise forms.ValidationError("PAN number is required")
        
        # Basic PAN format validation
        import re
        pan_pattern = r'^[A-Z]{5}[0-9]{4}[A-Z]{1}$'
        if not re.match(pan_pattern, pan):
            raise forms.ValidationError("Invalid PAN format. Use: ABCDE1234F")
        
        # Check if this PAN already exists
        pan_hash = PANRecord.generate_hash(pan)
        existing = PANRecord.objects.filter(pan_hash=pan_hash)
        
        # Exclude current instance if editing
        if self.instance.pk:
            existing = existing.exclude(pk=self.instance.pk)
        
        if existing.exists():
            raise forms.ValidationError("This PAN number is already registered")
        
        return pan
    
    def save(self, commit=True):
        """Override save to generate hash and last_4 from full number"""
        instance = super().save(commit=False)
        
        full_pan = self.cleaned_data.get('full_pan_number')
        if full_pan:
            instance.pan_hash = PANRecord.generate_hash(full_pan)
            instance.pan_last_4 = full_pan[-4:]
        
        if commit:
            instance.save()
        return instance


# ==========================================
# ADMIN CONFIGURATION FOR NEOBANK MODELS
# ==========================================

@admin.register(CustomUser)
class CustomUserAdmin(admin.ModelAdmin):
    """
    Admin interface for CustomUser model.
    
    Features:
    - List display shows key user information
    - Search and filtering capabilities
    - Readonly fields for sensitive data
    - Organized fieldsets for better UX
    """
    list_display = ('username', 'email', 'phone', 'is_phone_verified', 'date_joined', 'is_active')
    list_filter = ('is_phone_verified', 'is_active', 'date_joined')
    search_fields = ('username', 'email', 'phone', 'first_name', 'last_name')
    readonly_fields = ('date_joined', 'last_login', 'pan_masked', 'aadhaar_masked')
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('username', 'email', 'first_name', 'last_name')
        }),
        ('Contact Information', {
            'fields': ('phone', 'is_phone_verified')
        }),
        ('KYC Information (Read-only)', {
            'fields': ('pan_masked', 'aadhaar_masked'),
            'classes': ('collapse',),
            'description': 'KYC information is automatically populated during signup verification.'
        }),
        ('Permissions', {
            'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions'),
            'classes': ('collapse',),
        }),
        ('Important Dates', {
            'fields': ('last_login', 'date_joined'),
            'classes': ('collapse',),
        }),
    )


@admin.register(AadhaarRecord)
class AadhaarRecordAdmin(admin.ModelAdmin):
    """
    Admin interface for managing pre-approved Aadhaar records.
    
    This is the key interface where admins can add Aadhaar numbers
    that will be accepted during the signup verification process.
    
    Features:
    - Easy addition of new Aadhaar records with full number input
    - Automatic hash generation and security masking
    - Search and filtering capabilities
    - Bulk actions for management
    - Security-focused display (no full numbers shown)
    """
    form = AadhaarRecordForm  # Use custom form
    
    list_display = ('full_name', 'aadhaar_last_4_display', 'date_of_birth', 'gender', 'pin_code', 'is_active', 'created_at', 'created_by')
    list_filter = ('gender', 'is_active', 'created_at', 'created_by', 'pin_code')
    search_fields = ('full_name', 'aadhaar_last_4', 'address_line', 'pin_code')
    readonly_fields = ('aadhaar_hash', 'aadhaar_last_4', 'created_at', 'updated_at')
    ordering = ('-created_at',)
    
    # Updated fieldsets to show the custom form field
    fieldsets = (
        ('Aadhaar Information', {
            'fields': ('full_aadhaar_number',),
            'description': 'Enter the complete 12-digit Aadhaar number. It will be hashed and only last 4 digits stored.'
        }),
        ('Personal Details', {
            'fields': ('full_name', 'date_of_birth', 'gender')
        }),
        ('Address Information', {
            'fields': ('address_line', 'pin_code')
        }),
        ('Administrative', {
            'fields': ('is_active',),
            'classes': ('collapse',),
            'description': 'Created by will be set automatically to current admin user.'
        }),
        ('Security Information (Read-only)', {
            'fields': ('aadhaar_last_4', 'aadhaar_hash'),
            'classes': ('collapse',),
            'description': 'Auto-generated security fields - do not edit manually.'
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )
    
    # Special fieldset for edit forms (when hash already exists)
    def get_fieldsets(self, request, obj=None):
        """
        Return different fieldsets for add vs edit forms
        """
        if obj:  # Editing existing record
            return (
                ('Aadhaar Information', {
                    'fields': (),
                    'description': 'Aadhaar number cannot be changed for security reasons.'
                }),
                ('Personal Details', {
                    'fields': ('full_name', 'date_of_birth', 'gender')
                }),
                ('Address Information', {
                    'fields': ('address_line', 'pin_code')
                }),
                ('Administrative', {
                    'fields': ('is_active', 'created_by'),
                    'classes': ('collapse',)
                }),
                ('Security Information (Read-only)', {
                    'fields': ('aadhaar_last_4', 'aadhaar_hash'),
                    'classes': ('collapse',),
                    'description': 'Auto-generated security fields.'
                }),
                ('Timestamps', {
                    'fields': ('created_at', 'updated_at'),
                    'classes': ('collapse',)
                })
            )
        else:  # Adding new record
            return self.fieldsets
    
    def get_form(self, request, obj=None, **kwargs):
        """
        Return different forms for add vs edit
        """
        if obj:  # Editing existing record
            # Use default form without full_aadhaar_number field
            form = super().get_form(request, obj, **kwargs)
            return form
        else:  # Adding new record
            return self.form
    
    def save_model(self, request, obj, form, change):
        """
        Override save to set created_by for new records
        """
        if not change:  # New record
            obj.created_by = request.user.username
        super().save_model(request, obj, form, change)
    
    actions = ['activate_records', 'deactivate_records']
    
    def aadhaar_last_4_display(self, obj):
        """Display masked Aadhaar for security"""
        return f"****-****-{obj.aadhaar_last_4}"
    aadhaar_last_4_display.short_description = "Aadhaar (Masked)"
    
    def activate_records(self, request, queryset):
        """Bulk action to activate Aadhaar records"""
        count = queryset.update(is_active=True)
        self.message_user(request, f'{count} Aadhaar records activated.')
    activate_records.short_description = "Activate selected Aadhaar records"
    
    def deactivate_records(self, request, queryset):
        """Bulk action to deactivate Aadhaar records"""
        count = queryset.update(is_active=False)
        self.message_user(request, f'{count} Aadhaar records deactivated.')
    deactivate_records.short_description = "Deactivate selected Aadhaar records"
    
    def save_model(self, request, obj, form, change):
        """Auto-generate hash when saving Aadhaar record"""
        # Set created_by to current user if not already set
        if not obj.created_by:
            obj.created_by = request.user.username
        
        # If aadhaar_hash is not set, we need the full number to generate it
        # In a real implementation, you'd have a secure form field for the full number
        # For this demo, we'll show how it would work
        if not obj.aadhaar_hash and hasattr(form, 'full_aadhaar_number'):
            full_number = form.full_aadhaar_number
            obj.aadhaar_hash = AadhaarRecord.generate_hash(full_number)
            obj.aadhaar_last_4 = full_number[-4:]
        
        super().save_model(request, obj, form, change)


@admin.register(PANRecord)
class PANRecordAdmin(admin.ModelAdmin):
    """
    Admin interface for managing pre-approved PAN records.
    
    Similar to AadhaarRecord, this allows admins to manage PAN numbers
    that will be accepted during verification.
    """
    form = PANRecordForm  # Use custom form
    
    list_display = ('full_name', 'pan_last_4_display', 'date_of_birth', 'pan_status', 'is_active', 'created_at', 'created_by')
    list_filter = ('pan_status', 'is_active', 'created_at', 'created_by')
    search_fields = ('full_name', 'pan_last_4', 'father_name')
    readonly_fields = ('pan_hash', 'pan_last_4', 'created_at', 'updated_at')
    ordering = ('-created_at',)
    
    fieldsets = (
        ('PAN Information', {
            'fields': ('full_pan_number', 'pan_status'),
            'description': 'Enter the complete PAN number. It will be hashed and only last 4 characters stored.'
        }),
        ('Personal Details', {
            'fields': ('full_name', 'date_of_birth', 'father_name')
        }),
        ('Administrative', {
            'fields': ('is_active',),
            'classes': ('collapse',),
            'description': 'Created by will be set automatically to current admin user.'
        }),
        ('Security Information (Read-only)', {
            'fields': ('pan_last_4', 'pan_hash'),
            'classes': ('collapse',),
            'description': 'Auto-generated security fields - do not edit manually.'
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )
    
    def get_fieldsets(self, request, obj=None):
        """Return different fieldsets for add vs edit forms"""
        if obj:  # Editing existing record
            return (
                ('PAN Information', {
                    'fields': ('pan_status',),
                    'description': 'PAN number cannot be changed for security reasons.'
                }),
                ('Personal Details', {
                    'fields': ('full_name', 'date_of_birth', 'father_name')
                }),
                ('Administrative', {
                    'fields': ('is_active', 'created_by'),
                    'classes': ('collapse',)
                }),
                ('Security Information (Read-only)', {
                    'fields': ('pan_last_4', 'pan_hash'),
                    'classes': ('collapse',),
                }),
                ('Timestamps', {
                    'fields': ('created_at', 'updated_at'),
                    'classes': ('collapse',)
                })
            )
        else:  # Adding new record
            return self.fieldsets
    
    def get_form(self, request, obj=None, **kwargs):
        """Return different forms for add vs edit"""
        if obj:  # Editing existing record
            form = super().get_form(request, obj, **kwargs)
            return form
        else:  # Adding new record
            return self.form
    
    def save_model(self, request, obj, form, change):
        """
        Override save to set created_by for new records
        """
        if not change:  # New record
            obj.created_by = request.user.username
        super().save_model(request, obj, form, change)
    
    actions = ['activate_records', 'deactivate_records']
    
    def pan_last_4_display(self, obj):
        """Display masked PAN for security"""
        return f"XXXXX{obj.pan_last_4}"
    pan_last_4_display.short_description = "PAN (Masked)"
    
    def activate_records(self, request, queryset):
        """Bulk action to activate PAN records"""
        count = queryset.update(is_active=True)
        self.message_user(request, f'{count} PAN records activated.')
    activate_records.short_description = "Activate selected PAN records"
    
    def deactivate_records(self, request, queryset):
        """Bulk action to deactivate PAN records"""
        count = queryset.update(is_active=False)
        self.message_user(request, f'{count} PAN records deactivated.')
    deactivate_records.short_description = "Deactivate selected PAN records"
    
    def save_model(self, request, obj, form, change):
        """Auto-generate hash when saving PAN record"""
        if not obj.created_by:
            obj.created_by = request.user.username
        super().save_model(request, obj, form, change)


@admin.register(SignupSession)
class SignupSessionAdmin(admin.ModelAdmin):
    """
    Admin interface for monitoring signup sessions.
    
    Useful for debugging signup issues and monitoring the process.
    """
    list_display = ('session_id_short', 'phone', 'current_step', 'is_completed', 'created_at', 'updated_at')
    list_filter = ('current_step', 'is_completed', 'created_at')
    search_fields = ('phone', 'session_id')
    readonly_fields = ('session_id', 'created_at', 'updated_at', 'data')
    ordering = ('-created_at',)
    
    fieldsets = (
        ('Session Information', {
            'fields': ('session_id', 'phone', 'current_step', 'is_completed')
        }),
        ('OTP Information (Demo)', {
            'fields': ('otp_code', 'otp_expires_at', 'otp_attempts'),
            'description': 'In production, OTP would be stored securely (hashed) in Redis.'
        }),
        ('Session Data', {
            'fields': ('data',),
            'classes': ('collapse',),
            'description': 'JSON data containing step information.'
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )
    
    def session_id_short(self, obj):
        """Display shortened session ID for readability"""
        return f"{str(obj.session_id)[:8]}..."
    session_id_short.short_description = "Session ID"


@admin.register(KYCRecord)
class KYCRecordAdmin(admin.ModelAdmin):
    """
    Admin interface for KYC verification records.
    
    Provides audit trail for all KYC verification attempts.
    """
    list_display = ('session_id_short', 'provider', 'status', 'created_at')
    list_filter = ('provider', 'status', 'created_at')
    search_fields = ('session__phone', 'provider', 'status')
    readonly_fields = ('session', 'provider', 'status', 'response', 'created_at')
    ordering = ('-created_at',)
    
    def session_id_short(self, obj):
        """Display shortened session ID"""
        return f"{str(obj.session.session_id)[:8]}..."
    session_id_short.short_description = "Session ID"
    
    def has_add_permission(self, request):
        """KYC records are created automatically - no manual addition"""
        return False


@admin.register(Account)
class AccountAdmin(admin.ModelAdmin):
    """
    Admin interface for user accounts.
    """
    list_display = ('account_number', 'user', 'display_name', 'created_at')
    list_filter = ('created_at',)
    search_fields = ('account_number', 'user__username', 'user__email', 'user__phone', 'display_name')
    readonly_fields = ('created_at',)
    ordering = ('-created_at',)
    
    fieldsets = (
        ('Account Information', {
            'fields': ('user', 'account_number', 'display_name')
        }),
        ('Timestamps', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        })
    )


# ==========================================
# ADMIN SITE CUSTOMIZATION
# ==========================================

# Customize admin site headers
admin.site.site_header = 'NeoBank Administration'
admin.site.site_title = 'NeoBank Admin'
admin.site.index_title = 'Welcome to NeoBank Administration'

# Add helpful descriptions
admin.site.site_url = None  # Remove "View Site" link for security

from django import forms
from django.core.validators import RegexValidator
from django.utils import timezone
from datetime import date, timedelta


class MobileVerificationForm(forms.Form):
    """Form for mobile number verification (Step 1)"""
    country_code = forms.ChoiceField(
        choices=[('+91', '+91 (India)')],
        initial='+91',
        widget=forms.Select(attrs={
            'class': 'form-input w-full rounded-2xl border border-white/10 bg-slate-900/60 px-4 py-3 focus:ring-2 focus:ring-teal-500/50'
        })
    )
    phone = forms.CharField(
        max_length=10,
        min_length=10,
        validators=[RegexValidator(r'^\d{10}$', 'Enter a valid 10-digit mobile number')],
        widget=forms.TextInput(attrs={
            'class': 'form-input w-full rounded-2xl border border-white/10 bg-slate-900/60 pl-12 pr-4 py-3 outline-none focus:ring-2 focus:ring-teal-500/50',
            'placeholder': 'Enter your mobile number',
            'inputmode': 'numeric',
            'maxlength': '10'
        })
    )


class OTPVerificationForm(forms.Form):
    """Reusable form for OTP verification"""
    otp = forms.CharField(
        max_length=6,
        min_length=6,
        validators=[RegexValidator(r'^\d{6}$', 'Enter a valid 6-digit OTP')],
        widget=forms.TextInput(attrs={
            'class': 'form-input w-full rounded-2xl border border-white/10 bg-slate-900/60 px-4 py-3 text-center text-2xl font-mono tracking-widest focus:ring-2 focus:ring-teal-500/50',
            'placeholder': '000000',
            'inputmode': 'numeric',
            'maxlength': '6'
        })
    )


class PersonalDetailsForm(forms.Form):
    """Form for personal details (Step 2)"""
    full_name = forms.CharField(
        max_length=100,
        min_length=2,
        widget=forms.TextInput(attrs={
            'class': 'form-input w-full rounded-2xl border border-white/10 bg-slate-900/60 pl-12 pr-4 py-3 outline-none focus:ring-2 focus:ring-teal-500/50',
            'placeholder': 'Enter your full name as per government ID'
        })
    )
    email = forms.EmailField(
        widget=forms.EmailInput(attrs={
            'class': 'form-input w-full rounded-2xl border border-white/10 bg-slate-900/60 pl-12 pr-4 py-3 outline-none focus:ring-2 focus:ring-teal-500/50',
            'placeholder': 'your.email@example.com'
        })
    )
    date_of_birth = forms.DateField(
        widget=forms.DateInput(attrs={
            'class': 'form-input w-full rounded-2xl border border-white/10 bg-slate-900/60 pl-12 pr-4 py-3 outline-none focus:ring-2 focus:ring-teal-500/50',
            'type': 'date'
        })
    )
    gender = forms.ChoiceField(
        choices=[('', 'Select Gender'), ('M', 'Male'), ('F', 'Female'), ('O', 'Other')],
        widget=forms.Select(attrs={
            'class': 'form-input w-full rounded-2xl border border-white/10 bg-slate-900/60 pl-12 pr-10 py-3 outline-none focus:ring-2 focus:ring-teal-500/50 appearance-none'
        })
    )

    def clean_date_of_birth(self):
        dob = self.cleaned_data.get('date_of_birth')
        if dob:
            today = date.today()
            age = today.year - dob.year - ((today.month, today.day) < (dob.month, dob.day))
            if age < 18:
                raise forms.ValidationError("You must be at least 18 years old to create an account.")
        return dob


class AadhaarVerificationForm(forms.Form):
    """Form for Aadhaar verification (Step 3)"""
    aadhaar_number = forms.CharField(
        max_length=14,  # Allow for spaces in formatting
        min_length=12,
        validators=[RegexValidator(r'^\d{4}\s?\d{4}\s?\d{4}$', 'Enter a valid 12-digit Aadhaar number')],
        widget=forms.TextInput(attrs={
            'class': 'form-input w-full rounded-2xl border border-white/10 bg-slate-900/60 pl-12 pr-4 py-3 outline-none focus:ring-2 focus:ring-orange-500/50 tracking-wider text-lg font-mono',
            'placeholder': 'Enter your 12-digit Aadhaar number',
            'inputmode': 'numeric',
            'maxlength': '14'
        })
    )
    current_address = forms.CharField(
        widget=forms.Textarea(attrs={
            'class': 'form-input w-full rounded-2xl border border-white/10 bg-slate-900/60 pl-12 pr-4 py-3 outline-none focus:ring-2 focus:ring-orange-500/50 resize-none',
            'placeholder': 'Enter your current residential address',
            'rows': 3
        })
    )
    aadhaar_consent = forms.BooleanField(
        required=True,
        widget=forms.CheckboxInput(attrs={
            'class': 'h-5 w-5 rounded border-white/20 bg-slate-900/60 text-orange-500 focus:ring-orange-500/50 focus:ring-2'
        })
    )

    def clean_aadhaar_number(self):
        aadhaar = self.cleaned_data.get('aadhaar_number')
        if aadhaar:
            # Remove spaces and validate
            clean_aadhaar = aadhaar.replace(' ', '')
            if len(clean_aadhaar) != 12 or not clean_aadhaar.isdigit():
                raise forms.ValidationError("Enter a valid 12-digit Aadhaar number.")
            return clean_aadhaar
        return aadhaar


class PANVerificationForm(forms.Form):
    """Form for PAN verification (Step 4)"""
    pan_number = forms.CharField(
        max_length=10,
        min_length=10,
        validators=[RegexValidator(r'^[A-Z]{5}[0-9]{4}[A-Z]$', 'Enter a valid PAN number (format: ABCDE1234F)')],
        widget=forms.TextInput(attrs={
            'class': 'form-input w-full rounded-2xl border border-white/10 bg-slate-900/60 pl-12 pr-4 py-3 outline-none focus:ring-2 focus:ring-purple-500/50 uppercase tracking-widest text-lg font-mono',
            'placeholder': 'Enter your 10-character PAN number',
            'maxlength': '10',
            'autocomplete': 'off'
        })
    )
    pan_consent = forms.BooleanField(
        required=True,
        widget=forms.CheckboxInput(attrs={
            'class': 'h-5 w-5 rounded border-white/20 bg-slate-900/60 text-purple-500 focus:ring-purple-500/50 focus:ring-2'
        })
    )

    def clean_pan_number(self):
        pan = self.cleaned_data.get('pan_number')
        if pan:
            return pan.upper()


class PINSetupForm(forms.Form):
    """Form for PIN setup (Step 5)"""
    pin = forms.CharField(
        max_length=6,
        min_length=6,
        validators=[RegexValidator(r'^\d{6}$', 'PIN must be exactly 6 digits')],
        widget=forms.PasswordInput(attrs={
            'class': 'form-input w-full rounded-2xl border border-white/10 bg-slate-900/60 pl-12 pr-4 py-3 outline-none focus:ring-2 focus:ring-emerald-500/50 text-center text-2xl font-mono tracking-widest',
            'placeholder': 'Enter 6-digit PIN',
            'inputmode': 'numeric',
            'maxlength': '6'
        })
    )
    confirm_pin = forms.CharField(
        max_length=6,
        min_length=6,
        validators=[RegexValidator(r'^\d{6}$', 'PIN must be exactly 6 digits')],
        widget=forms.PasswordInput(attrs={
            'class': 'form-input w-full rounded-2xl border border-white/10 bg-slate-900/60 pl-12 pr-4 py-3 outline-none focus:ring-2 focus:ring-emerald-500/50 text-center text-2xl font-mono tracking-widest',
            'placeholder': 'Confirm 6-digit PIN',
            'inputmode': 'numeric',
            'maxlength': '6'
        })
    )
    terms = forms.BooleanField(
        required=True,
        widget=forms.CheckboxInput(attrs={
            'class': 'h-5 w-5 rounded border-white/20 bg-slate-900/60 text-emerald-500 focus:ring-emerald-500/50 focus:ring-2'
        })
    )

    def clean(self):
        cleaned_data = super().clean()
        pin = cleaned_data.get('pin')
        confirm_pin = cleaned_data.get('confirm_pin')

        if pin and confirm_pin:
            if pin != confirm_pin:
                raise forms.ValidationError("PINs do not match. Please try again.")
            
            # Check for weak PINs
            if pin in ['123456', '000000', '111111', '654321']:
                raise forms.ValidationError("Please choose a more secure PIN. Avoid common patterns.")

        return cleaned_data


class LoginForm(forms.Form):
    """Form for user login"""
    mobile = forms.CharField(
        max_length=10,
        min_length=10,
        validators=[RegexValidator(r'^\d{10}$', 'Enter a valid 10-digit mobile number')],
        widget=forms.TextInput(attrs={
            'class': 'form-input w-full rounded-2xl border border-white/10 bg-slate-900/60 pl-12 pr-4 py-3 outline-none focus:ring-2 focus:ring-teal-500/50',
            'placeholder': 'Enter your mobile number',
            'inputmode': 'numeric',
            'maxlength': '10'
        })
    )
    pin = forms.CharField(
        max_length=6,
        min_length=6,
        validators=[RegexValidator(r'^\d{6}$', 'PIN must be exactly 6 digits')],
        widget=forms.PasswordInput(attrs={
            'class': 'form-input w-full rounded-2xl border border-white/10 bg-slate-900/60 pl-12 pr-4 py-3 outline-none focus:ring-2 focus:ring-teal-500/50 text-center text-2xl font-mono tracking-widest',
            'placeholder': 'Enter 6-digit PIN',
            'inputmode': 'numeric',
            'maxlength': '6'
        })
    )

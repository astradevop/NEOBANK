from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth import login as auth_login, logout as auth_logout
from django.utils import timezone
from django.db import transaction
from django.core.exceptions import ValidationError
from .models import CustomUser, Account, SignupProgress
from .forms import (
    MobileVerificationForm, OTPVerificationForm, PersonalDetailsForm,
    AadhaarVerificationForm, PANVerificationForm, PINSetupForm, LoginForm
)
from .utils import (
    generate_otp, send_otp_sms, verify_aadhaar, verify_pan,
    generate_account_number, generate_customer_id, mask_aadhaar, mask_pan,
    calculate_credit_score, generate_username, format_phone_number,
    get_expiry_time, is_signup_expired, get_next_step_url, get_previous_step_url
)


def signup_redirect(request):
    """Redirect to appropriate signup step or start from step 1"""
    session_id = request.session.get('signup_session_id')
    
    if session_id:
        try:
            signup_progress = SignupProgress.objects.get(session_id=session_id)
            if not is_signup_expired(signup_progress.expires_at):
                # Resume from where user left off
                next_step_url = get_next_step_url(signup_progress.current_step)
                return redirect(next_step_url)
            else:
                # Session expired, clean up and start fresh
                signup_progress.delete()
                del request.session['signup_session_id']
        except SignupProgress.DoesNotExist:
            pass
    
    # Start fresh from step 1
    return redirect('accounts:signup_step1')


def signup_step1(request):
    """Step 1: Mobile verification"""
    current_step = 1
    progress_percentage = 20
    
    # Get or create signup session
    session_id = request.session.get('signup_session_id')
    if not session_id:
        session_id = f"signup_{request.session.session_key}_{timezone.now().timestamp()}"
        request.session['signup_session_id'] = session_id
    
    try:
        signup_progress = SignupProgress.objects.get(session_id=session_id)
    except SignupProgress.DoesNotExist:
        signup_progress = SignupProgress.objects.create(
            session_id=session_id,
            current_step=1,
            expires_at=get_expiry_time()
        )
    
    # Check if mobile is already verified
    if signup_progress.mobile_verified:
        return redirect('accounts:signup_step2')
    
    mobile_form = MobileVerificationForm()
    otp_form = OTPVerificationForm()
    otp_sent = False
    phone_display = ""
    
    if request.method == 'POST':
        action = request.POST.get('action')
        
        if action == 'send_otp':
            mobile_form = MobileVerificationForm(request.POST)
            if mobile_form.is_valid():
                phone = mobile_form.cleaned_data['phone']
                country_code = mobile_form.cleaned_data['country_code']
                
                # Generate and send OTP
                otp = generate_otp()
                send_otp_sms(phone, otp, "mobile verification")
                
                # Save to signup progress
                signup_progress.phone = phone
                signup_progress.country_code = country_code
                signup_progress.mobile_otp = otp
                signup_progress.save()
                
                otp_sent = True
                phone_display = format_phone_number(phone, country_code)
                messages.success(request, f"OTP sent to {phone_display}")
        
        elif action == 'verify_otp':
            # Get OTP from individual inputs
            otp_digits = [request.POST.get(f'otp_{i}', '') for i in range(1, 7)]
            otp = ''.join(otp_digits)
            
            if len(otp) == 6 and otp.isdigit():
                if otp == signup_progress.mobile_otp:
                    # OTP verified successfully
                    signup_progress.mobile_verified = True
                    signup_progress.mobile_verified_at = timezone.now()
                    signup_progress.current_step = 2
                    signup_progress.save()
                    
                    messages.success(request, "Mobile number verified successfully!")
                    return redirect('accounts:signup_step2')
                else:
                    messages.error(request, "Invalid OTP. Please try again.")
            else:
                messages.error(request, "Please enter a valid 6-digit OTP.")
            
            otp_sent = True
            phone_display = format_phone_number(signup_progress.phone, signup_progress.country_code)
    
    context = {
        'current_step': current_step,
        'progress_percentage': progress_percentage,
        'mobile_form': mobile_form,
        'otp_form': otp_form,
        'otp_sent': otp_sent,
        'phone_display': phone_display,
    }
    
    return render(request, 'accounts/signup/step1_mobile.html', context)


def signup_step2(request):
    """Step 2: Personal details"""
    current_step = 2
    progress_percentage = 40
    
    session_id = request.session.get('signup_session_id')
    if not session_id:
        return redirect('accounts:signup_step1')
    
    try:
        signup_progress = SignupProgress.objects.get(session_id=session_id)
    except SignupProgress.DoesNotExist:
        return redirect('accounts:signup_step1')
    
    # Check if mobile is verified
    if not signup_progress.mobile_verified:
        return redirect('accounts:signup_step1')
    
    # Pre-populate form with existing data
    initial_data = {
        'full_name': signup_progress.full_name,
        'email': signup_progress.email,
        'date_of_birth': signup_progress.date_of_birth,
        'gender': signup_progress.gender,
    }
    
    form = PersonalDetailsForm(initial=initial_data)
    
    if request.method == 'POST':
        form = PersonalDetailsForm(request.POST)
        if form.is_valid():
            # Save personal details
            signup_progress.full_name = form.cleaned_data['full_name']
            signup_progress.email = form.cleaned_data['email']
            signup_progress.date_of_birth = form.cleaned_data['date_of_birth']
            signup_progress.gender = form.cleaned_data['gender']
            signup_progress.current_step = 3
            signup_progress.save()
            
            messages.success(request, "Personal details saved successfully!")
            return redirect('accounts:signup_step3')
    
    context = {
        'current_step': current_step,
        'progress_percentage': progress_percentage,
        'form': form,
    }
    
    return render(request, 'accounts/signup/step2_personal.html', context)


def signup_step3(request):
    """Step 3: Aadhaar verification"""
    current_step = 3
    progress_percentage = 60
    
    session_id = request.session.get('signup_session_id')
    if not session_id:
        return redirect('accounts:signup_step1')
    
    try:
        signup_progress = SignupProgress.objects.get(session_id=session_id)
    except SignupProgress.DoesNotExist:
        return redirect('accounts:signup_step1')
    
    # Check if previous steps are completed
    if not signup_progress.mobile_verified or not signup_progress.full_name:
        return redirect('accounts:signup_step2')
    
    # Check if Aadhaar is already verified
    if signup_progress.aadhaar_verified:
        return redirect('accounts:signup_step4')
    
    # Pre-populate form with existing data
    initial_data = {
        'aadhaar_number': signup_progress.aadhaar_number,
        'current_address': signup_progress.current_address,
    }
    
    form = AadhaarVerificationForm(initial=initial_data)
    otp_form = OTPVerificationForm()
    otp_sent = False
    masked_aadhaar = ""
    aadhaar_name = ""
    
    if request.method == 'POST':
        action = request.POST.get('action')
        
        if action == 'verify_aadhaar':
            form = AadhaarVerificationForm(request.POST)
            if form.is_valid():
                aadhaar_number = form.cleaned_data['aadhaar_number']
                current_address = form.cleaned_data['current_address']
                
                # Verify Aadhaar (mock verification)
                verification_result = verify_aadhaar(aadhaar_number, signup_progress.full_name)
                
                if verification_result['success']:
                    # Generate and send OTP
                    otp = generate_otp()
                    send_otp_sms(signup_progress.phone, otp, "Aadhaar verification")
                    
                    # Save to signup progress
                    signup_progress.aadhaar_number = aadhaar_number
                    signup_progress.current_address = current_address
                    signup_progress.aadhaar_otp = otp
                    signup_progress.aadhaar_name = verification_result['name_on_aadhaar']
                    signup_progress.save()
                    
                    otp_sent = True
                    masked_aadhaar = verification_result['masked_aadhaar']
                    aadhaar_name = verification_result['name_on_aadhaar']
                    messages.success(request, "Aadhaar details verified! Please enter the OTP sent to your mobile.")
                else:
                    messages.error(request, verification_result['message'])
        
        elif action == 'verify_otp':
            # Get OTP from individual inputs
            otp_digits = [request.POST.get(f'otp_{i}', '') for i in range(1, 7)]
            otp = ''.join(otp_digits)
            
            if len(otp) == 6 and otp.isdigit():
                if otp == signup_progress.aadhaar_otp:
                    # OTP verified successfully
                    signup_progress.aadhaar_verified = True
                    signup_progress.aadhaar_verified_at = timezone.now()
                    signup_progress.current_step = 4
                    signup_progress.save()
                    
                    messages.success(request, "Aadhaar verification completed successfully!")
                    return redirect('accounts:signup_step4')
                else:
                    messages.error(request, "Invalid OTP. Please try again.")
            else:
                messages.error(request, "Please enter a valid 6-digit OTP.")
            
            otp_sent = True
            masked_aadhaar = mask_aadhaar(signup_progress.aadhaar_number)
            aadhaar_name = signup_progress.aadhaar_name
    
    context = {
        'current_step': current_step,
        'progress_percentage': progress_percentage,
        'form': form,
        'otp_form': otp_form,
        'otp_sent': otp_sent,
        'masked_aadhaar': masked_aadhaar,
        'aadhaar_name': aadhaar_name,
    }
    
    return render(request, 'accounts/signup/step3_aadhaar.html', context)


def signup_step4(request):
    """Step 4: PAN verification"""
    current_step = 4
    progress_percentage = 80
    
    session_id = request.session.get('signup_session_id')
    if not session_id:
        return redirect('accounts:signup_step1')
    
    try:
        signup_progress = SignupProgress.objects.get(session_id=session_id)
    except SignupProgress.DoesNotExist:
        return redirect('accounts:signup_step1')
    
    # Check if previous steps are completed
    if not signup_progress.aadhaar_verified:
        return redirect('accounts:signup_step3')
    
    # Check if PAN is already verified
    if signup_progress.pan_verified:
        return redirect('accounts:signup_step5')
    
    # Pre-populate form with existing data
    initial_data = {
        'pan_number': signup_progress.pan_number,
    }
    
    form = PANVerificationForm(initial=initial_data)
    otp_form = OTPVerificationForm()
    otp_sent = False
    masked_pan = ""
    pan_name = ""
    
    if request.method == 'POST':
        action = request.POST.get('action')
        
        if action == 'verify_pan':
            form = PANVerificationForm(request.POST)
            if form.is_valid():
                pan_number = form.cleaned_data['pan_number']
                
                # Verify PAN (mock verification)
                verification_result = verify_pan(pan_number, signup_progress.full_name)
                
                if verification_result['success']:
                    # Generate and send OTP
                    otp = generate_otp()
                    send_otp_sms(signup_progress.phone, otp, "PAN verification")
                    
                    # Save to signup progress
                    signup_progress.pan_number = pan_number
                    signup_progress.pan_otp = otp
                    signup_progress.pan_name = verification_result['name_on_pan']
                    signup_progress.save()
                    
                    otp_sent = True
                    masked_pan = verification_result['masked_pan']
                    pan_name = verification_result['name_on_pan']
                    messages.success(request, "PAN details verified! Please enter the OTP sent to your mobile.")
                else:
                    messages.error(request, verification_result['message'])
        
        elif action == 'verify_otp':
            # Get OTP from individual inputs
            otp_digits = [request.POST.get(f'otp_{i}', '') for i in range(1, 7)]
            otp = ''.join(otp_digits)
            
            if len(otp) == 6 and otp.isdigit():
                if otp == signup_progress.pan_otp:
                    # OTP verified successfully
                    signup_progress.pan_verified = True
                    signup_progress.pan_verified_at = timezone.now()
                    signup_progress.current_step = 5
                    signup_progress.save()
                    
                    messages.success(request, "PAN verification completed successfully!")
                    return redirect('accounts:signup_step5')
                else:
                    messages.error(request, "Invalid OTP. Please try again.")
            else:
                messages.error(request, "Please enter a valid 6-digit OTP.")
            
            otp_sent = True
            masked_pan = mask_pan(signup_progress.pan_number)
            pan_name = signup_progress.pan_name
    
    context = {
        'current_step': current_step,
        'progress_percentage': progress_percentage,
        'form': form,
        'otp_form': otp_form,
        'otp_sent': otp_sent,
        'masked_pan': masked_pan,
        'pan_name': pan_name,
    }
    
    return render(request, 'accounts/signup/step4_pan.html', context)


def signup_step5(request):
    """Step 5: PIN setup and account creation"""
    current_step = 5
    progress_percentage = 100
    
    session_id = request.session.get('signup_session_id')
    if not session_id:
        return redirect('accounts:signup_step1')
    
    try:
        signup_progress = SignupProgress.objects.get(session_id=session_id)
    except SignupProgress.DoesNotExist:
        return redirect('accounts:signup_step1')
    
    # Check if previous steps are completed
    if not signup_progress.pan_verified:
        return redirect('accounts:signup_step4')
    
    form = PINSetupForm()
    
    if request.method == 'POST':
        form = PINSetupForm(request.POST)
        if form.is_valid():
            pin = form.cleaned_data['pin']
            
            # Create user account
            with transaction.atomic():
                # Generate username and customer ID
                username = generate_username(signup_progress.full_name, signup_progress.phone)
                customer_id = generate_customer_id()
                
                # Create user
                user = CustomUser.objects.create_user(
                    username=username,
                    mobile=signup_progress.phone,
                    email=signup_progress.email,
                    customer_id=customer_id,
                    full_name=signup_progress.full_name,
                    date_of_birth=signup_progress.date_of_birth,
                    gender=signup_progress.gender,
                    aadhaar_number=signup_progress.aadhaar_number,
                    pan_number=signup_progress.pan_number,
                    current_address=signup_progress.current_address,
                    pin=int(pin),
                    terms_accepted_at=timezone.now(),
                    account_status='approved',  # Auto-approve for demo
                    credit_score=calculate_credit_score({
                        'date_of_birth': signup_progress.date_of_birth
                    })
                )
                
                # Create account
                account_number = generate_account_number()
                account = Account.objects.create(
                    user=user,
                    account_number=account_number,
                    balance=0.00,
                    account_type='savings'
                )
                
                # Clean up signup progress
                signup_progress.delete()
                del request.session['signup_session_id']
                
                # Store account details for success page
                request.session['account_details'] = {
                    'customer_id': user.customer_id,
                    'username': user.username,
                    'account_number': account.account_number,
                    'full_name': user.full_name,
                    'email': user.email,
                    'phone': user.mobile,
                    'created_at': user.created_at.isoformat(),  # Convert datetime to string
                    'credit_score': user.credit_score,
                    'approved_limit': 50000,  # Demo limit
                }
                
                messages.success(request, "Account created successfully!")
                return redirect('accounts:signup_success')
    
    context = {
        'current_step': current_step,
        'progress_percentage': progress_percentage,
        'form': form,
    }
    
    return render(request, 'accounts/signup/step5_pin.html', context)


def signup_success(request):
    """Success page showing account details"""
    account_details = request.session.get('account_details')
    
    if not account_details:
        return redirect('accounts:signup_step1')
    
    # Clear the session data after showing success
    del request.session['account_details']
    
    context = {
        'account_details': account_details,
    }
    
    return render(request, 'accounts/signup/success.html', context)


def login(request):
    if request.method == 'POST':
        form = LoginForm(request.POST)
        if form.is_valid():
            mobile = form.cleaned_data['mobile']
            pin = form.cleaned_data['pin']
            
            try:
                # Find user by mobile number
                user = CustomUser.objects.get(mobile=mobile)
                
                # Check if PIN matches
                if user.pin == int(pin):
                    # Login successful
                    auth_login(request, user)
                    messages.success(request, f"Welcome back, {user.full_name}!")
                    return redirect('dashboard:home')  # Redirect to dashboard/home
                else:
                    messages.error(request, "Invalid PIN. Please try again.")
            except CustomUser.DoesNotExist:
                messages.error(request, "No account found with this mobile number.")
    else:
        form = LoginForm()
    
    return render(request, 'accounts/login.html', {'form': form})


def logout(request):
    """Logout view"""
    auth_logout(request)
    messages.success(request, "You have been logged out successfully!")
    return redirect('index')

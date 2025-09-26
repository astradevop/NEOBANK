# users/views.py
"""
Views for the NeoBank signup flow - Step 1: Mobile OTP Verification

This file implements the backend logic for the first step of the signup process:
1. send_otp() - Generates and "sends" OTP (prints to console for demo)
2. verify_otp() - Validates the OTP code entered by user

Key Learning Points:
- How to handle AJAX/API requests in Django
- Session management for multi-step forms
- OTP generation and validation
- JSON API responses
- Basic security practices (rate limiting, expiry)
"""

import random
import json
from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.utils import timezone
from .models import SignupSession

# ==========================================
# TEMPLATE VIEWS (existing functionality)
# ==========================================

def signup(request):
    """
    Render the signup template.
    This is the main signup page that contains the multi-step form.
    """
    return render(request, 'users/signup.html')

def login(request):
    """
    Render the login template.
    """
    return render(request, 'users/login.html')

# ==========================================
# API ENDPOINTS FOR OTP FUNCTIONALITY
# ==========================================

@csrf_exempt  # For demo purposes - in production, use proper CSRF handling
@require_http_methods(["POST"])  # Only allow POST requests
def send_otp(request):
    """
    API endpoint to generate and "send" OTP to user's phone.
    
    Process:
    1. Extract phone number from request
    2. Validate phone number format
    3. Generate 6-digit OTP
    4. Store OTP in SignupSession model
    5. Print OTP to console (demo mode)
    6. Return success response
    
    Request body (JSON):
    {
        "phone": "9876543210",
        "country_code": "+91"  # optional
    }
    
    Response (JSON):
    {
        "success": true,
        "message": "OTP sent successfully",
        "session_id": "uuid-string",
        "expires_in": 300  # seconds
    }
    """
    try:
        # Parse JSON data from request body
        data = json.loads(request.body)
        phone = data.get('phone', '').strip()
        country_code = data.get('country_code', '+91')
        
        # Basic validation
        if not phone:
            return JsonResponse({
                'success': False,
                'message': 'Phone number is required'
            }, status=400)
        
        # Clean phone number (remove non-digits for storage)
        phone_digits = ''.join(filter(str.isdigit, phone))
        
        # Basic phone validation (should be 10 digits for Indian numbers)
        if len(phone_digits) < 8 or len(phone_digits) > 15:
            return JsonResponse({
                'success': False,
                'message': 'Please enter a valid phone number'
            }, status=400)
        
        # Generate 6-digit OTP
        otp_code = str(random.randint(100000, 999999))
        
        # Find existing session or create new one
        # This allows users to resend OTP for the same phone number
        session, created = SignupSession.objects.get_or_create(
            phone=phone_digits,
            is_completed=False,
            defaults={
                'current_step': 1,
                'data': {'country_code': country_code}
            }
        )
        
        # Set OTP with 5-minute expiry
        session.set_otp(otp_code, ttl_seconds=300)
        
        # 🎯 DEMO: Print OTP to console (as requested by user)
        print("\n" + "="*50)
        print(f"📱 OTP for {country_code}{phone_digits}: {otp_code}")
        print(f"📅 Expires at: {session.otp_expires_at}")
        print(f"🆔 Session ID: {session.session_id}")
        print("="*50 + "\n")
        
        # In production, you would integrate with SMS providers like:
        # - Twilio
        # - AWS SNS
        # - MSG91
        # - TextLocal
        # Example: send_sms(phone_digits, f"Your NeoBank OTP: {otp_code}")
        
        return JsonResponse({
            'success': True,
            'message': 'OTP sent successfully',
            'session_id': str(session.session_id),
            'expires_in': 300
        })
        
    except json.JSONDecodeError:
        return JsonResponse({
            'success': False,
            'message': 'Invalid JSON data'
        }, status=400)
        
    except Exception as e:
        # Log error in production
        print(f"Error in send_otp: {str(e)}")
        return JsonResponse({
            'success': False,
            'message': 'An error occurred. Please try again.'
        }, status=500)


@csrf_exempt  # For demo purposes
@require_http_methods(["POST"])
def verify_otp(request):
    """
    API endpoint to verify the OTP entered by user.
    
    Process:
    1. Extract session_id and otp_code from request
    2. Find the corresponding SignupSession
    3. Validate OTP using the session's verify_otp method
    4. Update session state if verification succeeds
    5. Return appropriate response
    
    Request body (JSON):
    {
        "session_id": "uuid-string",
        "otp_code": "123456"
    }
    
    Response (JSON):
    Success:
    {
        "success": true,
        "message": "OTP verified successfully",
        "next_step": 2
    }
    
    Failure:
    {
        "success": false,
        "message": "Invalid OTP",
        "attempts_left": 2
    }
    """
    try:
        # Parse request data
        data = json.loads(request.body)
        session_id = data.get('session_id')
        otp_code = data.get('otp_code', '').strip()
        
        # Validate required fields
        if not session_id or not otp_code:
            return JsonResponse({
                'success': False,
                'message': 'Session ID and OTP code are required'
            }, status=400)
        
        # Find the signup session
        try:
            session = SignupSession.objects.get(
                session_id=session_id,
                is_completed=False
            )
        except SignupSession.DoesNotExist:
            return JsonResponse({
                'success': False,
                'message': 'Invalid or expired session'
            }, status=404)
        
        # Rate limiting: Check if too many failed attempts
        MAX_ATTEMPTS = 3
        if session.otp_attempts >= MAX_ATTEMPTS:
            return JsonResponse({
                'success': False,
                'message': 'Too many failed attempts. Please request a new OTP.',
                'should_resend': True
            }, status=429)
        
        # Verify OTP using the model's method
        is_valid, error_reason = session.verify_otp(otp_code)
        
        if is_valid:
            # 🎯 Success! OTP verified
            print("\n" + "✅"*20)
            print(f"✅ OTP VERIFIED for session {session.session_id}")
            print(f"✅ Phone: {session.phone}")
            print(f"✅ Moving to step: {session.current_step}")
            print("✅"*20 + "\n")
            
            return JsonResponse({
                'success': True,
                'message': 'OTP verified successfully',
                'next_step': session.current_step,
                'session_id': str(session.session_id)
            })
        
        else:
            # OTP verification failed
            error_messages = {
                'no_otp': 'No OTP found. Please request a new one.',
                'expired': 'OTP has expired. Please request a new one.',
                'wrong': 'Invalid OTP. Please try again.'
            }
            
            attempts_left = MAX_ATTEMPTS - session.otp_attempts
            
            print(f"\n❌ OTP verification failed: {error_reason}")
            print(f"❌ Attempts remaining: {attempts_left}")
            print(f"❌ Session: {session.session_id}\n")
            
            response_data = {
                'success': False,
                'message': error_messages.get(error_reason, 'OTP verification failed'),
                'attempts_left': max(0, attempts_left)
            }
            
            # If expired or no OTP, suggest resending
            if error_reason in ['expired', 'no_otp']:
                response_data['should_resend'] = True
            
            return JsonResponse(response_data, status=400)
            
    except json.JSONDecodeError:
        return JsonResponse({
            'success': False,
            'message': 'Invalid JSON data'
        }, status=400)
        
    except Exception as e:
        # Log error in production
        print(f"Error in verify_otp: {str(e)}")
        return JsonResponse({
            'success': False,
            'message': 'An error occurred. Please try again.'
        }, status=500)


# ==========================================
# API ENDPOINTS FOR PERSONAL DETAILS (STEP 2)
# ==========================================

@csrf_exempt  # For demo purposes
@require_http_methods(["POST"])
def save_personal_details(request):
    """
    API endpoint to save personal details in Step 2 of signup.
    
    This function handles the second step of the NeoBank signup process where
    users provide their personal information for KYC verification.
    
    Process Flow:
    1. Validate session ID to ensure user completed Step 1 (OTP verification)
    2. Extract and validate personal details from request
    3. Perform basic data validation (name, email, date of birth, gender)
    4. Store the validated data in the SignupSession's data field
    5. Update the current_step to 3 to allow progression
    6. Return success response to frontend
    
    Request Body (JSON):
    {
        "session_id": "uuid-string",
        "full_name": "John Doe",
        "email": "john.doe@example.com",
        "date_of_birth": "1990-01-15",
        "gender": "M"  # M/F/O
    }
    
    Response (JSON):
    Success:
    {
        "success": true,
        "message": "Personal details saved successfully",
        "next_step": 3,
        "session_id": "uuid-string"
    }
    
    Failure:
    {
        "success": false,
        "message": "Error description"
    }
    
    Learning Points:
    - How to validate multi-field form data
    - JSON field usage for storing flexible data structures
    - Email validation using Django's built-in validators
    - Date validation and parsing
    - Progressive form completion tracking
    """
    try:
        # Step 1: Parse the incoming JSON data
        data = json.loads(request.body)
        session_id = data.get('session_id')
        
        # Step 2: Validate session exists and user is on correct step
        if not session_id:
            return JsonResponse({
                'success': False,
                'message': 'Session ID is required'
            }, status=400)
        
        try:
            session = SignupSession.objects.get(
                session_id=session_id,
                is_completed=False
            )
        except SignupSession.DoesNotExist:
            return JsonResponse({
                'success': False,
                'message': 'Invalid or expired session'
            }, status=404)
        
        # Step 3: Check if user has completed Step 1 (OTP verification)
        if session.current_step < 2:
            return JsonResponse({
                'success': False,
                'message': 'Please complete mobile verification first'
            }, status=400)
        
        # Step 4: Extract personal details from request
        full_name = data.get('full_name', '').strip()
        email = data.get('email', '').strip()
        date_of_birth = data.get('date_of_birth', '').strip()
        gender = data.get('gender', '').strip()
        
        # Step 5: Validate required fields
        if not full_name:
            return JsonResponse({
                'success': False,
                'message': 'Full name is required'
            }, status=400)
        
        if not email:
            return JsonResponse({
                'success': False,
                'message': 'Email address is required'
            }, status=400)
        
        if not date_of_birth:
            return JsonResponse({
                'success': False,
                'message': 'Date of birth is required'
            }, status=400)
        
        if not gender or gender not in ['M', 'F', 'O']:
            return JsonResponse({
                'success': False,
                'message': 'Please select a valid gender'
            }, status=400)
        
        # Step 6: Validate full name format
        if len(full_name) < 2:
            return JsonResponse({
                'success': False,
                'message': 'Full name must be at least 2 characters'
            }, status=400)
        
        if len(full_name) > 100:
            return JsonResponse({
                'success': False,
                'message': 'Full name is too long'
            }, status=400)
        
        # Step 7: Validate email format using Django's validator
        from django.core.validators import validate_email
        from django.core.exceptions import ValidationError
        
        try:
            validate_email(email)
        except ValidationError:
            return JsonResponse({
                'success': False,
                'message': 'Please enter a valid email address'
            }, status=400)
        
        # Step 8: Validate date of birth
        from datetime import datetime, date
        
        try:
            # Parse date string (expecting YYYY-MM-DD format)
            dob_date = datetime.strptime(date_of_birth, '%Y-%m-%d').date()
            
            # Check if date is not in the future
            if dob_date > date.today():
                return JsonResponse({
                    'success': False,
                    'message': 'Date of birth cannot be in the future'
                }, status=400)
            
            # Check minimum age (18 years for bank account)
            today = date.today()
            age = today.year - dob_date.year - ((today.month, today.day) < (dob_date.month, dob_date.day))
            
            if age < 18:
                return JsonResponse({
                    'success': False,
                    'message': 'You must be at least 18 years old to create an account'
                }, status=400)
            
            if age > 120:  # Reasonable upper limit
                return JsonResponse({
                    'success': False,
                    'message': 'Please enter a valid date of birth'
                }, status=400)
                
        except ValueError:
            return JsonResponse({
                'success': False,
                'message': 'Please enter a valid date in YYYY-MM-DD format'
            }, status=400)
        
        # Step 9: Store personal details in session data
        # We use the JSON field to store step-specific data flexibly
        if 'personal_details' not in session.data:
            session.data['personal_details'] = {}
        
        session.data['personal_details'] = {
            'full_name': full_name,
            'email': email,
            'date_of_birth': date_of_birth,
            'gender': gender,
            'saved_at': timezone.now().isoformat(),  # Track when this step was completed
        }
        
        # Step 10: Progress to next step (Aadhaar verification)
        session.current_step = max(session.current_step, 3)
        session.save()
        
        # Step 11: Log success for debugging
        print("\n" + "📝"*30)
        print(f"📝 PERSONAL DETAILS SAVED for session {session.session_id}")
        print(f"📝 Name: {full_name}")
        print(f"📝 Email: {email}")
        print(f"📝 DOB: {date_of_birth}")
        print(f"📝 Gender: {gender}")
        print(f"📝 Moving to step: {session.current_step}")
        print("📝"*30 + "\n")
        
        # Step 12: Return success response
        return JsonResponse({
            'success': True,
            'message': 'Personal details saved successfully',
            'next_step': session.current_step,
            'session_id': str(session.session_id)
        })
        
    except json.JSONDecodeError:
        return JsonResponse({
            'success': False,
            'message': 'Invalid JSON data'
        }, status=400)
        
    except Exception as e:
        # Log error for debugging
        print(f"Error in save_personal_details: {str(e)}")
        return JsonResponse({
            'success': False,
            'message': 'An error occurred while saving personal details. Please try again.'
        }, status=500)


# ==========================================
# API ENDPOINTS FOR AADHAAR VERIFICATION (STEP 3)
# ==========================================

@csrf_exempt  # For demo purposes
@require_http_methods(["POST"])
def verify_aadhaar(request):
    """
    API endpoint to verify Aadhaar details in Step 3 of signup.
    
    This function implements Aadhaar verification with a two-step process:
    1. Validate Aadhaar number against pre-approved records (admin managed)
    2. Send OTP for Aadhaar verification (demo: printed to console)
    
    Process Flow:
    1. Validate session and ensure user completed Step 2 (personal details)
    2. Extract and validate Aadhaar number and address
    3. Check if Aadhaar exists in AadhaarRecord (admin pre-approved)
    4. Cross-verify personal details with Aadhaar record
    5. Generate Aadhaar OTP and store in session
    6. Print OTP to console (as requested)
    7. Return success response to proceed to OTP verification
    
    Request Body (JSON):
    {
        "session_id": "uuid-string",
        "aadhaar_number": "123456789012",
        "address": "Current address as provided by user"
    }
    
    Response (JSON):
    Success:
    {
        "success": true,
        "message": "Aadhaar details verified. OTP sent for final verification.",
        "masked_aadhaar": "XXXX-XXXX-9012",
        "otp_sent": true,
        "expires_in": 300
    }
    
    Failure:
    {
        "success": false,
        "message": "Aadhaar number not found or details mismatch"
    }
    
    Learning Points:
    - How to implement multi-step KYC verification
    - Cross-referencing user data with official records
    - Aadhaar number validation and formatting
    - Secure OTP generation for sensitive operations
    - Error handling for various verification scenarios
    """
    try:
        # Step 1: Parse incoming JSON data
        data = json.loads(request.body)
        session_id = data.get('session_id')
        aadhaar_number = data.get('aadhaar_number', '').strip()
        address = data.get('address', '').strip()
        
        # Step 2: Validate required fields
        if not session_id:
            return JsonResponse({
                'success': False,
                'message': 'Session ID is required'
            }, status=400)
        
        if not aadhaar_number:
            return JsonResponse({
                'success': False,
                'message': 'Aadhaar number is required'
            }, status=400)
        
        if not address:
            return JsonResponse({
                'success': False,
                'message': 'Current address is required'
            }, status=400)
        
        # Step 3: Validate session exists and user is on correct step
        try:
            session = SignupSession.objects.get(
                session_id=session_id,
                is_completed=False
            )
        except SignupSession.DoesNotExist:
            return JsonResponse({
                'success': False,
                'message': 'Invalid or expired session'
            }, status=404)
        
        # Step 4: Check if user has completed Step 2 (personal details)
        if session.current_step < 3:
            return JsonResponse({
                'success': False,
                'message': 'Please complete personal details first'
            }, status=400)
        
        # Step 5: Clean and validate Aadhaar number format
        aadhaar_digits = ''.join(filter(str.isdigit, aadhaar_number))
        
        if len(aadhaar_digits) != 12:
            return JsonResponse({
                'success': False,
                'message': 'Aadhaar number must be exactly 12 digits'
            }, status=400)
        
        # Step 6: Check if Aadhaar exists in pre-approved records
        from .models import AadhaarRecord
        
        # Generate hash to lookup Aadhaar record
        aadhaar_hash = AadhaarRecord.generate_hash(aadhaar_digits)
        
        try:
            aadhaar_record = AadhaarRecord.objects.get(
                aadhaar_hash=aadhaar_hash,
                is_active=True
            )
        except AadhaarRecord.DoesNotExist:
            return JsonResponse({
                'success': False,
                'message': 'Aadhaar number not found in our approved database. Please contact support.'
            }, status=404)
        
        # Step 7: Cross-verify personal details with Aadhaar record
        # Get personal details from Step 2
        personal_details = session.data.get('personal_details', {})
        
        if not personal_details:
            return JsonResponse({
                'success': False,
                'message': 'Personal details not found. Please complete Step 2 first.'
            }, status=400)
        
        # Verify name match (case-insensitive, basic matching)
        user_name = personal_details.get('full_name', '').lower().strip()
        aadhaar_name = aadhaar_record.full_name.lower().strip()
        
        if user_name != aadhaar_name:
            print(f"\n❌ NAME MISMATCH:")
            print(f"❌ User provided: '{user_name}'")
            print(f"❌ Aadhaar record: '{aadhaar_name}'")
            print(f"❌ Session: {session.session_id}\n")
            
            return JsonResponse({
                'success': False,
                'message': 'Name does not match with Aadhaar records. Please ensure your name matches exactly as per Aadhaar.'
            }, status=400)
        
        # Verify date of birth match
        user_dob = personal_details.get('date_of_birth')
        aadhaar_dob = aadhaar_record.date_of_birth.strftime('%Y-%m-%d')
        
        if user_dob != aadhaar_dob:
            print(f"\n❌ DOB MISMATCH:")
            print(f"❌ User provided: '{user_dob}'")
            print(f"❌ Aadhaar record: '{aadhaar_dob}'")
            print(f"❌ Session: {session.session_id}\n")
            
            return JsonResponse({
                'success': False,
                'message': 'Date of birth does not match with Aadhaar records.'
            }, status=400)
        
        # Verify gender match
        user_gender = personal_details.get('gender')
        aadhaar_gender = aadhaar_record.gender
        
        if user_gender != aadhaar_gender:
            print(f"\n❌ GENDER MISMATCH:")
            print(f"❌ User provided: '{user_gender}'")
            print(f"❌ Aadhaar record: '{aadhaar_gender}'")
            print(f"❌ Session: {session.session_id}\n")
            
            return JsonResponse({
                'success': False,
                'message': 'Gender does not match with Aadhaar records.'
            }, status=400)
        
        # Step 8: Generate Aadhaar verification OTP
        aadhaar_otp = str(random.randint(100000, 999999))
        
        # Step 9: Store Aadhaar verification data in session
        if 'aadhaar_verification' not in session.data:
            session.data['aadhaar_verification'] = {}
        
        session.data['aadhaar_verification'] = {
            'aadhaar_last_4': aadhaar_digits[-4:],
            'aadhaar_record_id': aadhaar_record.id,
            'address_provided': address,
            'otp_code': aadhaar_otp,  # In production, hash this!
            'otp_generated_at': timezone.now().isoformat(),
            'otp_expires_at': (timezone.now() + timezone.timedelta(seconds=300)).isoformat(),
            'otp_attempts': 0,
            'status': 'otp_sent'
        }
        
        # Don't progress step yet - wait for OTP verification
        session.save()
        
        # Step 10: 🎯 DEMO: Print Aadhaar OTP to console (as requested by user)
        print("\n" + "🔐"*50)
        print(f"🔐 AADHAAR VERIFICATION OTP")
        print(f"🔐 Aadhaar: XXXX-XXXX-{aadhaar_digits[-4:]}")
        print(f"🔐 Name: {aadhaar_record.full_name}")
        print(f"🔐 OTP Code: {aadhaar_otp}")
        print(f"🔐 Expires at: {session.data['aadhaar_verification']['otp_expires_at']}")
        print(f"🔐 Session ID: {session.session_id}")
        print("🔐"*50 + "\n")
        
        # Step 11: Log success for debugging
        print(f"\n✅ AADHAAR DETAILS VERIFIED for session {session.session_id}")
        print(f"✅ Name match: {aadhaar_record.full_name}")
        print(f"✅ DOB match: {aadhaar_dob}")
        print(f"✅ Gender match: {aadhaar_gender}")
        print(f"✅ OTP generated for final verification\n")
        
        # Step 12: Return success response
        return JsonResponse({
            'success': True,
            'message': 'Aadhaar details verified successfully. Please enter the OTP sent for final verification.',
            'masked_aadhaar': aadhaar_record.get_masked_aadhaar(),
            'name_on_aadhaar': aadhaar_record.full_name,
            'otp_sent': True,
            'expires_in': 300
        })
        
    except json.JSONDecodeError:
        return JsonResponse({
            'success': False,
            'message': 'Invalid JSON data'
        }, status=400)
        
    except Exception as e:
        # Log error for debugging
        print(f"Error in verify_aadhaar: {str(e)}")
        return JsonResponse({
            'success': False,
            'message': 'An error occurred while verifying Aadhaar. Please try again.'
        }, status=500)


@csrf_exempt  # For demo purposes
@require_http_methods(["POST"])
def verify_aadhaar_otp(request):
    """
    API endpoint to verify the OTP for Aadhaar verification.
    
    This is the second part of Step 3 - after Aadhaar details are verified,
    user enters the OTP to complete the Aadhaar verification process.
    
    Process Flow:
    1. Validate session and OTP code
    2. Check OTP expiry and attempt limits
    3. Verify the OTP matches stored value
    4. Update session to mark Aadhaar as verified
    5. Progress to Step 4 (PAN verification)
    6. Create KYC record for audit trail
    
    Request Body (JSON):
    {
        "session_id": "uuid-string",
        "otp_code": "123456"
    }
    
    Response (JSON):
    Success:
    {
        "success": true,
        "message": "Aadhaar verification completed successfully",
        "next_step": 4
    }
    
    Failure:
    {
        "success": false,
        "message": "Invalid OTP",
        "attempts_left": 2
    }
    
    Learning Points:
    - OTP verification patterns for sensitive operations
    - Session state management for multi-step processes
    - Rate limiting for security
    - Audit trail creation for KYC operations
    """
    try:
        # Step 1: Parse request data
        data = json.loads(request.body)
        session_id = data.get('session_id')
        otp_code = data.get('otp_code', '').strip()
        
        # Step 2: Validate required fields
        if not session_id or not otp_code:
            return JsonResponse({
                'success': False,
                'message': 'Session ID and OTP code are required'
            }, status=400)
        
        # Step 3: Find the signup session
        try:
            session = SignupSession.objects.get(
                session_id=session_id,
                is_completed=False
            )
        except SignupSession.DoesNotExist:
            return JsonResponse({
                'success': False,
                'message': 'Invalid or expired session'
            }, status=404)
        
        # Step 4: Check if Aadhaar verification was initiated
        aadhaar_verification = session.data.get('aadhaar_verification', {})
        
        if not aadhaar_verification or aadhaar_verification.get('status') != 'otp_sent':
            return JsonResponse({
                'success': False,
                'message': 'Aadhaar verification not initiated. Please complete Aadhaar details first.'
            }, status=400)
        
        # Step 5: Rate limiting - Check attempts
        MAX_ATTEMPTS = 3
        attempts = aadhaar_verification.get('otp_attempts', 0)
        
        if attempts >= MAX_ATTEMPTS:
            return JsonResponse({
                'success': False,
                'message': 'Too many failed attempts. Please restart Aadhaar verification.',
                'should_restart': True
            }, status=429)
        
        # Step 6: Check OTP expiry
        from datetime import datetime
        expiry_str = aadhaar_verification.get('otp_expires_at')
        
        if not expiry_str:
            return JsonResponse({
                'success': False,
                'message': 'OTP session expired. Please restart Aadhaar verification.'
            }, status=400)
        
        expiry_time = datetime.fromisoformat(expiry_str.replace('Z', '+00:00'))
        
        if timezone.now() > expiry_time:
            return JsonResponse({
                'success': False,
                'message': 'OTP has expired. Please restart Aadhaar verification.',
                'should_restart': True
            }, status=400)
        
        # Step 7: Verify OTP code
        stored_otp = aadhaar_verification.get('otp_code')
        
        if str(otp_code) != str(stored_otp):
            # Increment attempts
            session.data['aadhaar_verification']['otp_attempts'] = attempts + 1
            session.save()
            
            attempts_left = MAX_ATTEMPTS - (attempts + 1)
            
            print(f"\n❌ AADHAAR OTP verification failed: {otp_code} != {stored_otp}")
            print(f"❌ Attempts remaining: {attempts_left}")
            print(f"❌ Session: {session.session_id}\n")
            
            return JsonResponse({
                'success': False,
                'message': 'Invalid OTP. Please try again.',
                'attempts_left': max(0, attempts_left)
            }, status=400)
        
        # Step 8: 🎉 OTP verified successfully!
        # Update Aadhaar verification status
        session.data['aadhaar_verification']['status'] = 'verified'
        session.data['aadhaar_verification']['verified_at'] = timezone.now().isoformat()
        session.data['aadhaar_verification']['otp_code'] = None  # Clear OTP
        
        # Progress to next step (PAN verification)
        session.current_step = max(session.current_step, 4)
        session.save()
        
        # Step 9: Create KYC record for audit trail
        from .models import KYCRecord
        
        kyc_record = KYCRecord.objects.create(
            session=session,
            provider='aadhaar',
            status='success',
            response={
                'masked_aadhaar': f"XXXX-XXXX-{aadhaar_verification.get('aadhaar_last_4')}",
                'verification_method': 'otp',
                'verified_at': timezone.now().isoformat(),
                'address_provided': aadhaar_verification.get('address_provided', '')
            }
        )
        
        # Step 10: Log success
        print("\n" + "✅"*30)
        print(f"✅ AADHAAR VERIFICATION COMPLETED for session {session.session_id}")
        print(f"✅ Aadhaar: XXXX-XXXX-{aadhaar_verification.get('aadhaar_last_4')}")
        print(f"✅ KYC Record ID: {kyc_record.id}")
        print(f"✅ Moving to step: {session.current_step}")
        print("✅"*30 + "\n")
        
        # Step 11: Return success response
        return JsonResponse({
            'success': True,
            'message': 'Aadhaar verification completed successfully! 🎉',
            'next_step': session.current_step,
            'session_id': str(session.session_id),
            'masked_aadhaar': f"XXXX-XXXX-{aadhaar_verification.get('aadhaar_last_4')}"
        })
        
    except json.JSONDecodeError:
        return JsonResponse({
            'success': False,
            'message': 'Invalid JSON data'
        }, status=400)
        
    except Exception as e:
        # Log error for debugging
        print(f"Error in verify_aadhaar_otp: {str(e)}")
        return JsonResponse({
            'success': False,
            'message': 'An error occurred while verifying OTP. Please try again.'
        }, status=500)


# ==========================================
# API ENDPOINTS FOR PAN VERIFICATION (STEP 4)
# ==========================================

@csrf_exempt  # For demo purposes
@require_http_methods(["POST"])
def verify_pan(request):
    """
    API endpoint to verify PAN details in Step 4 of signup.
    
    This function implements PAN verification with a two-step process:
    1. Validate PAN number against pre-approved records (admin managed)
    2. Send OTP for PAN verification (demo: printed to console)
    
    Process Flow:
    1. Validate session and ensure user completed Step 3 (Aadhaar verification)
    2. Extract and validate PAN number and consent
    3. Check if PAN exists in PANRecord (admin pre-approved)
    4. Cross-verify personal details with PAN record
    5. Generate PAN OTP and store in session
    6. Print OTP to console (as requested)
    7. Return success response to proceed to OTP verification
    
    Request Body (JSON):
    {
        "session_id": "uuid-string",
        "pan_number": "ABCDE1234F",
        "consent": true
    }
    
    Response (JSON):
    Success:
    {
        "success": true,
        "message": "PAN details verified. OTP sent for final verification.",
        "masked_pan": "XXXXX1234F",
        "otp_sent": true,
        "expires_in": 300
    }
    
    Failure:
    {
        "success": false,
        "message": "PAN number not found or details mismatch"
    }
    
    Learning Points:
    - How to implement PAN verification for KYC compliance
    - Cross-referencing user data with official PAN records
    - PAN number validation and formatting
    - Secure OTP generation for sensitive operations
    - Error handling for various verification scenarios
    """
    try:
        # Step 1: Parse incoming JSON data
        data = json.loads(request.body)
        session_id = data.get('session_id')
        pan_number = data.get('pan_number', '').strip().upper()
        consent = data.get('consent', False)
        
        # Step 2: Validate required fields
        if not session_id:
            return JsonResponse({
                'success': False,
                'message': 'Session ID is required'
            }, status=400)
        
        if not pan_number:
            return JsonResponse({
                'success': False,
                'message': 'PAN number is required'
            }, status=400)
        
        if not consent:
            return JsonResponse({
                'success': False,
                'message': 'Please provide consent for PAN verification'
            }, status=400)
        
        # Step 3: Validate session exists and user is on correct step
        try:
            session = SignupSession.objects.get(
                session_id=session_id,
                is_completed=False
            )
        except SignupSession.DoesNotExist:
            return JsonResponse({
                'success': False,
                'message': 'Invalid or expired session'
            }, status=404)
        
        # Step 4: Check if user has completed Step 3 (Aadhaar verification)
        if session.current_step < 4:
            return JsonResponse({
                'success': False,
                'message': 'Please complete Aadhaar verification first'
            }, status=400)
        
        # Step 5: Validate PAN format (5 letters, 4 digits, 1 letter)
        import re
        PAN_REGEX = re.compile(r'^[A-Z]{5}[0-9]{4}[A-Z]$')
        
        if not PAN_REGEX.match(pan_number):
            return JsonResponse({
                'success': False,
                'message': 'Please enter a valid PAN number (format: ABCDE1234F)'
            }, status=400)
        
        # Step 6: Check if PAN exists in pre-approved records
        from .models import PANRecord
        
        # Generate hash to lookup PAN record
        pan_hash = PANRecord.generate_hash(pan_number)
        
        try:
            pan_record = PANRecord.objects.get(
                pan_hash=pan_hash,
                is_active=True
            )
        except PANRecord.DoesNotExist:
            return JsonResponse({
                'success': False,
                'message': 'PAN number not found in our approved database. Please contact support.'
            }, status=404)
        
        # Step 7: Cross-verify personal details with PAN record
        # Get personal details from Step 2
        personal_details = session.data.get('personal_details', {})
        
        if not personal_details:
            return JsonResponse({
                'success': False,
                'message': 'Personal details not found. Please complete Step 2 first.'
            }, status=400)
        
        # Verify name match (case-insensitive, basic matching)
        user_name = personal_details.get('full_name', '').lower().strip()
        pan_name = pan_record.full_name.lower().strip()
        
        if user_name != pan_name:
            print(f"\n❌ PAN NAME MISMATCH:")
            print(f"❌ User provided: '{user_name}'")
            print(f"❌ PAN record: '{pan_name}'")
            print(f"❌ Session: {session.session_id}\n")
            
            return JsonResponse({
                'success': False,
                'message': 'Name does not match with PAN records. Please ensure your name matches exactly as per PAN.'
            }, status=400)
        
        # Verify date of birth match
        user_dob = personal_details.get('date_of_birth')
        pan_dob = pan_record.date_of_birth.strftime('%Y-%m-%d')
        
        if user_dob != pan_dob:
            print(f"\n❌ PAN DOB MISMATCH:")
            print(f"❌ User provided: '{user_dob}'")
            print(f"❌ PAN record: '{pan_dob}'")
            print(f"❌ Session: {session.session_id}\n")
            
            return JsonResponse({
                'success': False,
                'message': 'Date of birth does not match with PAN records.'
            }, status=400)
        
        # Step 8: Generate PAN verification OTP
        pan_otp = str(random.randint(100000, 999999))
        
        # Step 9: Store PAN verification data in session
        if 'pan_verification' not in session.data:
            session.data['pan_verification'] = {}
        
        session.data['pan_verification'] = {
            'pan_last_4': pan_number[-4:],
            'pan_record_id': pan_record.id,
            'otp_code': pan_otp,  # In production, hash this!
            'otp_generated_at': timezone.now().isoformat(),
            'otp_expires_at': (timezone.now() + timezone.timedelta(seconds=300)).isoformat(),
            'otp_attempts': 0,
            'status': 'otp_sent'
        }
        
        # Don't progress step yet - wait for OTP verification
        session.save()
        
        # Step 10: 🎯 DEMO: Print PAN OTP to console (as requested by user)
        print("\n" + "💳"*50)
        print(f"💳 PAN VERIFICATION OTP")
        print(f"💳 PAN: XXXXX{pan_number[-4:]}")
        print(f"💳 Name: {pan_record.full_name}")
        print(f"💳 OTP Code: {pan_otp}")
        print(f"💳 Expires at: {session.data['pan_verification']['otp_expires_at']}")
        print(f"💳 Session ID: {session.session_id}")
        print("💳"*50 + "\n")
        
        # Step 11: Log success for debugging
        print(f"\n✅ PAN DETAILS VERIFIED for session {session.session_id}")
        print(f"✅ Name match: {pan_record.full_name}")
        print(f"✅ DOB match: {pan_dob}")
        print(f"✅ OTP generated for final verification\n")
        
        # Step 12: Return success response
        return JsonResponse({
            'success': True,
            'message': 'PAN details verified successfully. Please enter the OTP sent for final verification.',
            'masked_pan': pan_record.get_masked_pan(),
            'name_on_pan': pan_record.full_name,
            'otp_sent': True,
            'expires_in': 300
        })
        
    except json.JSONDecodeError:
        return JsonResponse({
            'success': False,
            'message': 'Invalid JSON data'
        }, status=400)
        
    except Exception as e:
        # Log error for debugging
        print(f"Error in verify_pan: {str(e)}")
        return JsonResponse({
            'success': False,
            'message': 'An error occurred while verifying PAN. Please try again.'
        }, status=500)


@csrf_exempt  # For demo purposes
@require_http_methods(["POST"])
def verify_pan_otp(request):
    """
    API endpoint to verify the OTP for PAN verification.
    
    This is the second part of Step 4 - after PAN details are verified,
    user enters the OTP to complete the PAN verification process.
    
    Process Flow:
    1. Validate session and OTP code
    2. Check OTP expiry and attempt limits
    3. Verify the OTP matches stored value
    4. Update session to mark PAN as verified
    5. Progress to Step 5 (Passcode setup)
    6. Create KYC record for audit trail
    
    Request Body (JSON):
    {
        "session_id": "uuid-string",
        "otp_code": "123456"
    }
    
    Response (JSON):
    Success:
    {
        "success": true,
        "message": "PAN verification completed successfully",
        "next_step": 5
    }
    
    Failure:
    {
        "success": false,
        "message": "Invalid OTP",
        "attempts_left": 2
    }
    
    Learning Points:
    - OTP verification patterns for sensitive operations
    - Session state management for multi-step processes
    - Rate limiting for security
    - Audit trail creation for KYC operations
    """
    try:
        # Step 1: Parse request data
        data = json.loads(request.body)
        session_id = data.get('session_id')
        otp_code = data.get('otp_code', '').strip()
        
        # Step 2: Validate required fields
        if not session_id or not otp_code:
            return JsonResponse({
                'success': False,
                'message': 'Session ID and OTP code are required'
            }, status=400)
        
        # Step 3: Find the signup session
        try:
            session = SignupSession.objects.get(
                session_id=session_id,
                is_completed=False
            )
        except SignupSession.DoesNotExist:
            return JsonResponse({
                'success': False,
                'message': 'Invalid or expired session'
            }, status=404)
        
        # Step 4: Check if PAN verification was initiated
        pan_verification = session.data.get('pan_verification', {})
        
        if not pan_verification or pan_verification.get('status') != 'otp_sent':
            return JsonResponse({
                'success': False,
                'message': 'PAN verification not initiated. Please complete PAN details first.'
            }, status=400)
        
        # Step 5: Rate limiting - Check attempts
        MAX_ATTEMPTS = 3
        attempts = pan_verification.get('otp_attempts', 0)
        
        if attempts >= MAX_ATTEMPTS:
            return JsonResponse({
                'success': False,
                'message': 'Too many failed attempts. Please restart PAN verification.',
                'should_restart': True
            }, status=429)
        
        # Step 6: Check OTP expiry
        from datetime import datetime
        expiry_str = pan_verification.get('otp_expires_at')
        
        if not expiry_str:
            return JsonResponse({
                'success': False,
                'message': 'OTP session expired. Please restart PAN verification.'
            }, status=400)
        
        expiry_time = datetime.fromisoformat(expiry_str.replace('Z', '+00:00'))
        
        if timezone.now() > expiry_time:
            return JsonResponse({
                'success': False,
                'message': 'OTP has expired. Please restart PAN verification.',
                'should_restart': True
            }, status=400)
        
        # Step 7: Verify OTP code
        stored_otp = pan_verification.get('otp_code')
        
        if str(otp_code) != str(stored_otp):
            # Increment attempts
            session.data['pan_verification']['otp_attempts'] = attempts + 1
            session.save()
            
            attempts_left = MAX_ATTEMPTS - (attempts + 1)
            
            print(f"\n❌ PAN OTP verification failed: {otp_code} != {stored_otp}")
            print(f"❌ Attempts remaining: {attempts_left}")
            print(f"❌ Session: {session.session_id}\n")
            
            return JsonResponse({
                'success': False,
                'message': 'Invalid OTP. Please try again.',
                'attempts_left': max(0, attempts_left)
            }, status=400)
        
        # Step 8: 🎉 OTP verified successfully!
        # Update PAN verification status
        session.data['pan_verification']['status'] = 'verified'
        session.data['pan_verification']['verified_at'] = timezone.now().isoformat()
        session.data['pan_verification']['otp_code'] = None  # Clear OTP
        
        # Progress to next step (Passcode setup)
        session.current_step = max(session.current_step, 5)
        session.save()
        
        # Step 9: Create KYC record for audit trail
        from .models import KYCRecord
        
        kyc_record = KYCRecord.objects.create(
            session=session,
            provider='pan',
            status='success',
            response={
                'masked_pan': f"XXXXX{pan_verification.get('pan_last_4')}",
                'verification_method': 'otp',
                'verified_at': timezone.now().isoformat()
            }
        )
        
        # Step 10: Log success
        print("\n" + "✅"*30)
        print(f"✅ PAN VERIFICATION COMPLETED for session {session.session_id}")
        print(f"✅ PAN: XXXXX{pan_verification.get('pan_last_4')}")
        print(f"✅ KYC Record ID: {kyc_record.id}")
        print(f"✅ Moving to step: {session.current_step}")
        print("✅"*30 + "\n")
        
        # Step 11: Return success response
        return JsonResponse({
            'success': True,
            'message': 'PAN verification completed successfully! 🎉',
            'next_step': session.current_step,
            'session_id': str(session.session_id),
            'masked_pan': f"XXXXX{pan_verification.get('pan_last_4')}"
        })
        
    except json.JSONDecodeError:
        return JsonResponse({
            'success': False,
            'message': 'Invalid JSON data'
        }, status=400)
        
    except Exception as e:
        # Log error for debugging
        print(f"Error in verify_pan_otp: {str(e)}")
        return JsonResponse({
            'success': False,
            'message': 'An error occurred while verifying OTP. Please try again.'
        }, status=500)


# ==========================================
# API ENDPOINTS FOR PIN SETUP (STEP 5)
# ==========================================

@csrf_exempt  # For demo purposes
@require_http_methods(["POST"])
def setup_pin(request):
    """
    API endpoint to set up PIN in Step 5 of signup.
    
    This function implements the final step of the NeoBank signup process where
    users create their 6-digit PIN for secure login and account access.
    
    Process Flow:
    1. Validate session and ensure user completed Step 4 (PAN verification)
    2. Extract and validate PIN and confirmation PIN
    3. Check PIN strength and security requirements
    4. Create the user account with all collected data
    5. Set the PIN securely (hashed)
    6. Create initial account record
    7. Mark signup session as completed
    8. Return success with account details
    
    Request Body (JSON):
    {
        "session_id": "uuid-string",
        "pin": "123456",
        "confirm_pin": "123456",
        "terms_accepted": true
    }
    
    Response (JSON):
    Success:
    {
        "success": true,
        "message": "Account created successfully! Welcome to NeoBank!",
        "account_details": {
            "username": "user123",
            "account_number": "NB1234567890",
            "full_name": "John Doe",
            "email": "john@example.com",
            "phone": "9876543210",
            "created_at": "2024-01-15T10:30:00Z"
        }
    }
    
    Failure:
    {
        "success": false,
        "message": "PINs do not match"
    }
    
    Learning Points:
    - How to complete a multi-step signup process
    - User account creation with secure PIN storage
    - Data aggregation from multiple signup steps
    - Account number generation
    - Session completion and cleanup
    - Security best practices for PIN handling
    """
    try:
        # Step 1: Parse incoming JSON data
        data = json.loads(request.body)
        session_id = data.get('session_id')
        pin = data.get('pin', '').strip()
        confirm_pin = data.get('confirm_pin', '').strip()
        terms_accepted = data.get('terms_accepted', False)
        
        # Step 2: Validate required fields
        if not session_id:
            return JsonResponse({
                'success': False,
                'message': 'Session ID is required'
            }, status=400)
        
        if not pin:
            return JsonResponse({
                'success': False,
                'message': 'PIN is required'
            }, status=400)
        
        if not confirm_pin:
            return JsonResponse({
                'success': False,
                'message': 'Please confirm your PIN'
            }, status=400)
        
        if not terms_accepted:
            return JsonResponse({
                'success': False,
                'message': 'Please accept the Terms and Privacy Policy'
            }, status=400)
        
        # Step 3: Validate PIN format
        if len(pin) != 6 or not pin.isdigit():
            return JsonResponse({
                'success': False,
                'message': 'PIN must be exactly 6 digits'
            }, status=400)
        
        # Step 4: Check PIN confirmation
        if pin != confirm_pin:
            return JsonResponse({
                'success': False,
                'message': 'PINs do not match. Please try again.'
            }, status=400)
        
        # Step 5: Basic PIN strength validation (avoid common patterns)
        if pin in ['123456', '000000', '111111', '654321', '123123']:
            return JsonResponse({
                'success': False,
                'message': 'Please choose a more secure PIN. Avoid common patterns like 123456.'
            }, status=400)
        
        # Step 6: Validate session exists and user is on correct step
        try:
            session = SignupSession.objects.get(
                session_id=session_id,
                is_completed=False
            )
        except SignupSession.DoesNotExist:
            return JsonResponse({
                'success': False,
                'message': 'Invalid or expired session'
            }, status=404)
        
        # Step 7: Check if user has completed Step 4 (PAN verification)
        if session.current_step < 5:
            return JsonResponse({
                'success': False,
                'message': 'Please complete PAN verification first'
            }, status=400)
        
        # Step 8: Verify all required data is present
        personal_details = session.data.get('personal_details', {})
        aadhaar_verification = session.data.get('aadhaar_verification', {})
        pan_verification = session.data.get('pan_verification', {})
        
        if not personal_details:
            return JsonResponse({
                'success': False,
                'message': 'Personal details not found. Please restart signup.'
            }, status=400)
        
        if not aadhaar_verification or aadhaar_verification.get('status') != 'verified':
            return JsonResponse({
                'success': False,
                'message': 'Aadhaar verification not completed. Please restart signup.'
            }, status=400)
        
        if not pan_verification or pan_verification.get('status') != 'verified':
            return JsonResponse({
                'success': False,
                'message': 'PAN verification not completed. Please restart signup.'
            }, status=400)
        
        # Step 9: Create the user account
        from .models import CustomUser, Account
        from django.contrib.auth import get_user_model
        
        # Generate unique username (phone-based for simplicity)
        username = f"user_{session.phone}"
        
        # Check if username already exists and make it unique
        counter = 1
        original_username = username
        while CustomUser.objects.filter(username=username).exists():
            username = f"{original_username}_{counter}"
            counter += 1
        
        # Create the user
        user = CustomUser.objects.create_user(
            username=username,
            email=personal_details.get('email'),
            first_name=personal_details.get('full_name', '').split()[0] if personal_details.get('full_name') else '',
            last_name=' '.join(personal_details.get('full_name', '').split()[1:]) if len(personal_details.get('full_name', '').split()) > 1 else '',
            phone=session.phone,
            is_phone_verified=True,
            pan_masked=f"XXXXX{pan_verification.get('pan_last_4', '****')}",
            aadhaar_masked=f"XXXX-XXXX-{aadhaar_verification.get('aadhaar_last_4', '****')}"
        )
        
        # Step 10: Set the PIN securely
        try:
            user.set_pin(pin)
        except ValueError as e:
            # If PIN setting fails, delete the user and return error
            user.delete()
            return JsonResponse({
                'success': False,
                'message': str(e)
            }, status=400)
        
        # Step 11: Create initial account
        import random
        account_number = f"NB{random.randint(1000000000, 9999999999)}"
        
        # Ensure account number is unique
        while Account.objects.filter(account_number=account_number).exists():
            account_number = f"NB{random.randint(1000000000, 9999999999)}"
        
        account = Account.objects.create(
            user=user,
            account_number=account_number,
            display_name="NeoBank Savings Account"
        )
        
        # Step 12: Mark signup session as completed
        session.is_completed = True
        session.data['final_user_id'] = user.id
        session.data['final_account_number'] = account_number
        session.data['completed_at'] = timezone.now().isoformat()
        session.save()
        
        # Step 13: Log success for debugging
        print("\n" + "🎉"*50)
        print(f"🎉 ACCOUNT CREATED SUCCESSFULLY!")
        print(f"🎉 User ID: {user.id}")
        print(f"🎉 Username: {username}")
        print(f"🎉 Account Number: {account_number}")
        print(f"🎉 Full Name: {personal_details.get('full_name')}")
        print(f"🎉 Email: {personal_details.get('email')}")
        print(f"🎉 Phone: {session.phone}")
        print(f"🎉 PIN Set: Yes (hashed)")
        print(f"🎉 Session: {session.session_id}")
        print("🎉"*50 + "\n")
        
        # Step 14: Return success response with account details
        return JsonResponse({
            'success': True,
            'message': 'Account created successfully! Welcome to NeoBank! 🎉',
            'account_details': {
                'user_id': user.id,
                'username': username,
                'account_number': account_number,
                'full_name': personal_details.get('full_name'),
                'email': personal_details.get('email'),
                'phone': session.phone,
                'created_at': user.date_joined.isoformat(),
                'pin_set': True
            }
        })
        
    except json.JSONDecodeError:
        return JsonResponse({
            'success': False,
            'message': 'Invalid JSON data'
        }, status=400)
        
    except Exception as e:
        # Log error for debugging
        print(f"Error in setup_pin: {str(e)}")
        return JsonResponse({
            'success': False,
            'message': 'An error occurred while creating your account. Please try again.'
        }, status=500)
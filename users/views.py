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
# users/urls.py
"""
URL patterns for the users app.

Routes:
- signup/ : Main signup template page
- login/ : Login template page  
- api/send-otp/ : API endpoint to send OTP via SMS (Step 1)
- api/verify-otp/ : API endpoint to verify OTP (Step 1)
- api/save-personal-details/ : API endpoint to save personal details (Step 2)

The api/ prefix helps organize API endpoints separately from template views.
This is a common Django pattern for mixed template + API applications.
"""

from django.urls import path
from users import views

app_name = "users"

urlpatterns = [
    # Template views (render HTML pages)
    path("signup/", views.signup, name="signup"),
    path("login/", views.login, name="login"),
    
    # API endpoints (return JSON responses)
    # These are called via AJAX from the frontend JavaScript
    
    # Step 1: Mobile OTP verification
    path("api/send-otp/", views.send_otp, name="send_otp"),
    path("api/verify-otp/", views.verify_otp, name="verify_otp"),
    
    # Step 2: Personal details collection
    path("api/save-personal-details/", views.save_personal_details, name="save_personal_details"),
    
    # Step 3: Aadhaar verification (two-part process)
    path("api/verify-aadhaar/", views.verify_aadhaar, name="verify_aadhaar"),
    path("api/verify-aadhaar-otp/", views.verify_aadhaar_otp, name="verify_aadhaar_otp"),
    
    # Step 4: PAN verification (two-part process)
    path("api/verify-pan/", views.verify_pan, name="verify_pan"),
    path("api/verify-pan-otp/", views.verify_pan_otp, name="verify_pan_otp"),
    
    # Step 5: PIN setup and account creation
    path("api/setup-pin/", views.setup_pin, name="setup_pin"),
]
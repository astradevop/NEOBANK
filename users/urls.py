# users/urls.py
"""
URL patterns for the users app.

Routes:
- signup/ : Main signup template page
- login/ : Login template page  
- api/send-otp/ : API endpoint to send OTP via SMS (Step 1)
- api/verify-otp/ : API endpoint to verify OTP (Step 1)

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
    path("api/send-otp/", views.send_otp, name="send_otp"),
    path("api/verify-otp/", views.verify_otp, name="verify_otp"),
]
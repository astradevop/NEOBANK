from django.urls import path
from . import views

app_name = 'accounts'

urlpatterns = [
    path('signup/', views.signup_redirect, name='signup'),
    path('signup/step1/', views.signup_step1, name='signup_step1'),
    path('signup/step2/', views.signup_step2, name='signup_step2'),
    path('signup/step3/', views.signup_step3, name='signup_step3'),
    path('signup/step4/', views.signup_step4, name='signup_step4'),
    path('signup/step5/', views.signup_step5, name='signup_step5'),
    path('signup/success/', views.signup_success, name='signup_success'),
    path('login/', views.login, name='login'),
    path('logout/', views.logout, name='logout'),
]
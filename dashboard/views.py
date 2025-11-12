from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from accounts.models import Account
from .models import UserPreference
from .utils import (
    get_credit_rating, calculate_monthly_spending, calculate_savings_rate,
    calculate_financial_health_score
)


@login_required
def dashboard_home(request):
    """Main dashboard view"""
    user = request.user
    
    try:
        account = user.account
    except Account.DoesNotExist:
        messages.error(request, "Account not found. Please contact support.")
        return redirect('index')
    
    # Get user preferences or create default
    preferences, created = UserPreference.objects.get_or_create(user=user)
    
    # Dashboard data
    context = {
        'user': user,
        'account': account,
        'customer_id': user.customer_id,
        
        # Account metrics
        'balance_trend': 5.2,
        'monthly_spending': calculate_monthly_spending(user),
        'spending_trend': -3.1,
        'savings_rate': calculate_savings_rate(user),
        'savings_pot_balance': 0.00,
        
        # Credit information
        'credit_score': user.credit_score,
        'credit_rating': get_credit_rating(user.credit_score),
        'credit_score_trend': 12,
        
        # Financial health
        'financial_health_score': calculate_financial_health_score(user),
        
        # Card information
        'credit_card_bill': 0.00,
        'credit_card_due_date': 'N/A',
        
        # Preferences
        'show_balance': preferences.show_balance,
        'show_credit_score': preferences.show_credit_score,
    }
    
    return render(request, 'dashboard/home.html', context)
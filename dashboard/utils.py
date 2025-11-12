from decimal import Decimal


def get_credit_rating(score):
    """Convert credit score to rating"""
    if score >= 750:
        return "Excellent"
    elif score >= 700:
        return "Good"
    elif score >= 650:
        return "Fair"
    else:
        return "Poor"


def calculate_monthly_spending(user):
    """Calculate spending for current month"""
    return Decimal('0.00')


def calculate_savings_rate(user):
    """Calculate savings rate"""
    return 0.0


def calculate_financial_health_score(user):
    """Calculate overall financial health score"""
    base_score = (user.credit_score / 850) * 100
    return min(base_score, 100)

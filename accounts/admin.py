from django.contrib import admin
from .models import CustomUser, Account


@admin.register(CustomUser)
class CustomUserAdmin(admin.ModelAdmin):
    list_display = ('customer_id', 'full_name', 'mobile', 'email', 'account_status', 'created_at')
    list_filter = ('account_status', 'created_at', 'gender')
    search_fields = ('customer_id', 'mobile', 'email', 'full_name', 'aadhaar_number', 'pan_number')
    readonly_fields = ('customer_id', 'created_at', 'updated_at', 'terms_accepted_at')
    ordering = ('-created_at',)
    
    fieldsets = (
        ('Customer Information', {
            'fields': ('customer_id', 'full_name', 'mobile', 'email', 'date_of_birth', 'gender')
        }),
        ('KYC Details', {
            'fields': ('aadhaar_number', 'pan_number', 'current_address')
        }),
        ('Account Status', {
            'fields': ('account_status', 'credit_score', 'pin', 'terms_accepted_at', 'account_approved_at')
        }),
        ('Permissions', {
            'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at')
        }),
    )


@admin.register(Account)
class AccountAdmin(admin.ModelAdmin):
    list_display = ('account_number', 'user_customer_id', 'user', 'balance', 'account_type', 'is_active', 'created_at')
    list_filter = ('account_type', 'is_active', 'created_at')
    search_fields = ('account_number', 'user__customer_id', 'user__mobile', 'user__full_name')
    readonly_fields = ('created_at', 'updated_at')
    
    def user_customer_id(self, obj):
        return obj.user.customer_id
    user_customer_id.short_description = 'Customer ID'
    user_customer_id.admin_order_field = 'user__customer_id'

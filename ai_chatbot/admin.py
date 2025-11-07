from django.contrib import admin
from .models import AIUsageWindow


@admin.register(AIUsageWindow)
class AIUsageWindowAdmin(admin.ModelAdmin):
    list_display = ['user', 'feature_type', 'date', 'usage_count']
    list_filter = ['feature_type', 'date']
    search_fields = ['user__email', 'user__first_name', 'user__last_name']
    date_hierarchy = 'date'
    readonly_fields = ['user', 'feature_type', 'date']

    actions = ['reset_usage']

    def reset_usage(self, request, queryset):
        """Reset usage count to 0 for selected windows"""
        count = queryset.update(usage_count=0)
        self.message_user(request, f"Reset {count} usage windows.")
    reset_usage.short_description = "Reset usage count to 0"

    def has_add_permission(self, request):
        """Prevent manual creation of usage windows"""
        return False

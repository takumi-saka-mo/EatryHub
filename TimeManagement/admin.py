from django.contrib import admin
from django.contrib.auth import get_user_model
from .models import TimeManagementRecord

CustomUser = get_user_model()

# 既に登録されている場合に回避
if not admin.site.is_registered(CustomUser):
    @admin.register(CustomUser)
    class CustomUserAdmin(admin.ModelAdmin):
        list_display = ('username', 'email', 'is_staff', 'is_active')

@admin.register(TimeManagementRecord)
class TimeManagementRecordAdmin(admin.ModelAdmin):
    list_display = ('date', 'row_number', 'table_number', 'plan_name', 'start_time', 'end_time', 'out_time')
    list_filter = ('date', 'store')
    search_fields = ('row_number', 'table_number', 'plan_name')
from django.contrib import admin
from django.contrib.auth import get_user_model
from .models import TimeManagementRecord
from django.http import HttpResponse
import csv
CustomUser = get_user_model()

# 既に登録されている場合に回避
if not admin.site.is_registered(CustomUser):
    @admin.register(CustomUser)
    class CustomUserAdmin(admin.ModelAdmin):
        list_display = ('username', 'email', 'is_staff', 'is_active')

# CSVエクスポートアクションの定義
def export_as_csv(modeladmin, request, queryset):
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="timemanagement_export.csv"'

    writer = csv.writer(response)
    # ヘッダー行（任意に調整）
    writer.writerow(['Date', 'Row Number', 'Table Number', 'Plan Name', 'Start Time', 'End Time', 'Out Time'])

    for obj in queryset:
        writer.writerow([
            obj.date,
            obj.row_number,
            obj.table_number,
            obj.plan_name,
            obj.start_time,
            obj.end_time,
            obj.out_time
        ])

    return response

export_as_csv.short_description = "CSVとしてエクスポート"

# TimeManagementRecord の管理設定
@admin.register(TimeManagementRecord)
class TimeManagementRecordAdmin(admin.ModelAdmin):
    list_display = ('date', 'row_number', 'table_number', 'plan_name', 'start_time', 'end_time', 'out_time')
    list_filter = ('date', 'store')
    search_fields = ('row_number', 'table_number', 'plan_name')
    actions = [export_as_csv]
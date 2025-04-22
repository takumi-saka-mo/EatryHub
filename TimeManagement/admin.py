from django.contrib import admin
from django.contrib.auth import get_user_model

CustomUser = get_user_model()

# 既に登録されている場合に回避
if not admin.site.is_registered(CustomUser):
    @admin.register(CustomUser)
    class CustomUserAdmin(admin.ModelAdmin):
        list_display = ('username', 'email', 'is_staff', 'is_active')
from django.urls import path
from .views import LoginView, LogoutView, index, home, mobile_view
from django.contrib import admin


app_name = 'EatryHub'

admin.site.site_title = '管理画面' 
admin.site.site_header = 'EatryHub - 管理画面' 
admin.site.index_title = 'メニュー'

urlpatterns = [
    path('', index, name='index'),
    path('login/', LoginView.as_view(), name='login'),
    path('logout/', LogoutView.as_view(), name='logout'),
    path('home/', home, name='home'),
    path("mobile/", mobile_view, name="mobile_view"),

]
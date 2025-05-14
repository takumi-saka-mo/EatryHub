from django.contrib import admin
from django.urls import path, include
from django.shortcuts import redirect
from EatryHub.views import mobile_view 

urlpatterns = [
    path('admin/', admin.site.urls),
    path('EatryHub/', include('EatryHub.urls')),
    path('TimeManagement/', include('TimeManagement.urls')),
    path('', lambda request: redirect('EatryHub:index')),
    path('mobile/', mobile_view),
]
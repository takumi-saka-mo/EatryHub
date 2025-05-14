from django.urls import path
from .views import LoginView, LogoutView, index, home, mobile_view

app_name = 'EatryHub'

urlpatterns = [
    path('', index, name='index'),
    path('login/', LoginView.as_view(), name='login'),
    path('logout/', LogoutView.as_view(), name='logout'),
    path('home/', home, name='home'),
    path("mobile/", mobile_view, name="mobile_view"),

]
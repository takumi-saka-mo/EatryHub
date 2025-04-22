from django.urls import path
from .views import LoginView, LogoutView, index, home

app_name = 'EatryHub'

urlpatterns = [
    path('', index, name='index'),
    path('login/', LoginView.as_view(), name='login'),
    path('logout/', LogoutView.as_view(), name='logout'),
    path('home/', home, name='home'),
]
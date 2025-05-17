from django.urls import path
from knox import views as knox_views
from . import views

app_name = 'accounts'

urlpatterns = [
    # مسارات المصادقة
    path('register/', views.RegisterView.as_view(), name='register'),
    path('login/', views.LoginView.as_view(), name='login'),
    path('logout/', knox_views.LogoutView.as_view(), name='logout'),
    path('logoutall/', knox_views.LogoutAllView.as_view(), name='logoutall'),
    
    # مسارات المستخدم
    path('profile/', views.UserDetailView.as_view(), name='profile'),
    path('change-password/', views.ChangePasswordView.as_view(), name='change-password'),
    path('technicians/', views.get_technicians, name='technicians'),
    path('update-profile/', views.UpdateProfileView.as_view(), name='update-profile'),
    path('toggle-availability/', views.toggle_availability, name='toggle-availability'),
    path('available-technicians/', views.get_available_technicians, name='available-technicians'),
    
    # Password Reset URLs
    path('password-reset/', views.PasswordResetRequestView.as_view(), name='password-reset-request'),
    path('password-reset-confirm/<str:uidb64>/<str:token>/', 
         views.PasswordResetConfirmView.as_view(), name='password-reset-confirm'),
]
from django.urls import path, reverse_lazy
from django.contrib.auth import views as auth_views
from . import views

app_name = 'core'

urlpatterns = [
    # Public pages
    path('', views.home, name='home'),  # Public home page
    path('services/', views.service_list, name='service_list'),  # Public services page
    path('services/request/', views.service_request, name='service_request'),  # Service request page
    path('services/request/submit/', views.submit_service_request, name='submit_service_request'),  # Submit service request
    path('tickets/', views.tickets, name='tickets'),  # Tickets page
    path('tickets/create/', views.create_ticket, name='ticket_create'),  # Create ticket endpoint
    path('tickets/<int:ticket_id>/', views.ticket_detail, name='ticket_detail'),  # Ticket detail page
    path('tickets/<int:ticket_id>/update/', views.update_ticket, name='ticket_update'),  # Update ticket endpoint
    path('services/<int:service_id>/', views.service_detail, name='service_detail'),  # Service detail page
    path('faq/', views.faq, name='faq'),  # FAQ page
    path('contact/', views.contact, name='contact'),  # Contact page
    
    # Dashboard (requires login)
    path('dashboard/', views.dashboard, name='dashboard'),
    path('technician/', views.technician_dashboard, name='technician_dashboard'),  # New URL for technician dashboard
    
    # Technician pages
    path('technician/tickets/', views.technician_tickets, name='technician_tickets'),
    path('technician/tickets/<int:ticket_id>/', views.technician_ticket_detail, name='technician_ticket_detail'),
    path('technician/tickets/create/', views.technician_create_ticket, name='technician_create_ticket'),
    path('technician/tickets/<int:ticket_id>/update/', views.technician_update_ticket, name='technician_update_ticket'),
    path('technician/tickets/<int:ticket_id>/resolve/', views.technician_resolve_ticket, name='technician_resolve_ticket'),
    path('technician/tickets/<int:ticket_id>/close/', views.technician_close_ticket, name='technician_close_ticket'),
    path('technician/tickets/<int:ticket_id>/transfer/', views.technician_transfer_ticket, name='technician_transfer_ticket'),
    path('technician/tickets/<int:ticket_id>/print/', views.technician_print_ticket, name='technician_print_ticket'),
    path('technician/tickets/<int:ticket_id>/assign/', views.technician_assign_ticket, name='technician_assign_ticket'),
    path('technician/tickets/<int:ticket_id>/escalate/', views.technician_escalate_ticket, name='technician_escalate_ticket'),
    path('technician/tickets/<int:ticket_id>/comment/', views.technician_add_comment, name='technician_add_comment'),
    path('technician/profile/', views.technician_profile, name='technician_profile'),
    path('technician/toggle-availability/', views.toggle_availability, name='toggle_availability'),
    path('technician/knowledge-base/', views.technician_knowledge_base, name='technician_knowledge_base'),
    path('technician/knowledge-base/article/<int:article_id>/', views.technician_article_detail, name='technician_article_detail'),
    path('technician/knowledge-base/article/<int:article_id>/feedback/', views.technician_article_feedback, name='technician_article_feedback'),
    path('technician/knowledge-base/create/', views.technician_create_article, name='technician_create_article'),
    path('technician/knowledge-base/article/<int:article_id>/edit/', views.technician_edit_article, name='technician_edit_article'),
    path('technician/knowledge-base/article/<int:article_id>/delete/', views.technician_delete_article, name='technician_delete_article'),
    
    # User management
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('register/', views.register, name='register'),
    
    # Email Verification
    path('verify-email/<str:uidb64>/<str:token>/', views.verify_email, name='verify_email'),
    path('email-verification-sent/', views.resend_verification, name='resend_verification'),
    
    # Password Reset
    path('password-reset/', auth_views.PasswordResetView.as_view(
        template_name='users/password_reset.html',
        email_template_name='users/email/password_reset_email.html',
        subject_template_name='users/email/password_reset_subject.txt',
        success_url=reverse_lazy('core:password_reset_done')
    ), name='password_reset'),
    path('password-reset/done/', auth_views.PasswordResetDoneView.as_view(
        template_name='users/password_reset_done.html'
    ), name='password_reset_done'),
    path('password-reset-confirm/<uidb64>/<token>/', auth_views.PasswordResetConfirmView.as_view(
        template_name='users/password_reset_confirm.html'
    ), name='password_reset_confirm'),
    path('password-reset-complete/', auth_views.PasswordResetCompleteView.as_view(
        template_name='users/password_reset_complete.html'
    ), name='password_reset_complete'),
    
    # Profile (requires login)
    path('profile/', views.profile, name='profile'),
    path('profile/update/', views.update_profile, name='update_profile'),
    path('profile/update-picture/', views.update_profile_picture, name='update_profile_picture'),
    path('profile/toggle-availability/', views.toggle_availability, name='toggle_availability'),
    path('profile/change-password/', views.change_password, name='change_password'),
    
    # Settings (requires login)
    path('settings/', views.settings, name='settings'),
    path('settings/notifications/', views.update_notification_settings, name='update_notification_settings'),
    path('settings/preferences/', views.update_preferences, name='update_preferences'),
    path('settings/privacy/', views.update_privacy, name='update_privacy'),
    path('settings/system/', views.update_system_settings, name='update_system_settings'),
    
    # Reset settings
    path('settings/reset-notifications/', views.reset_notification_settings, name='reset_notification_settings'),
    path('settings/reset-preferences/', views.reset_preferences, name='reset_preferences'),
    path('settings/reset-privacy/', views.reset_privacy, name='reset_privacy'),
    path('settings/reset-system/', views.reset_system_settings, name='reset_system_settings'),
]

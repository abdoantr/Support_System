from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, authenticate, update_session_auth_hash
from django.contrib.auth.decorators import login_required, user_passes_test
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.contrib import messages
from django.utils.http import urlsafe_base64_decode
from django.utils.encoding import force_str
from django.contrib.auth.tokens import default_token_generator
from django.core.exceptions import ValidationError
from django.db.models import Count
from django.utils import timezone
from datetime import timedelta
from django.views.decorators.csrf import ensure_csrf_cookie
from django.core.paginator import Paginator
from django.core.mail import send_mail
import datetime
import json
import logging
from django.db import models

from apps.accounts.models import User
from apps.services.models import Service
from apps.tickets.models import Ticket, TicketComment as Comment, TicketAttachment
from apps.kb.models import KnowledgeBaseArticle
from apps.profiles.models import TechnicianProfile
from .models import Profile, FAQ


# Import the forms we created
from .forms import (
    ContactForm, RegistrationForm, ProfileForm,
    CustomPasswordChangeForm, ServiceRequestForm,
    TicketForm, FAQFeedbackForm
)

logger = logging.getLogger(__name__)

# Helper function to check if user is a technician
def is_technician(user):
    """Check if user has technician role"""
    if user.is_authenticated:
        return hasattr(user, 'role') and user.role == 'technician'
    return False

def home(request):
    featured_services = Service.objects.filter(is_featured=True, is_active=True)[:6]
    
    # Get real counts instead of hardcoded values
    total_customers = User.objects.filter(role='customer').count()
    total_technicians = User.objects.filter(role='technician').count()
    total_tickets_resolved = Ticket.objects.filter(status='resolved').count()
    
    context = {
        'featured_services': featured_services,
        'total_customers': total_customers,
        'total_technicians': total_technicians,
        'total_tickets_resolved': total_tickets_resolved,
    }
    return render(request, 'home.html', context)

def service_list(request):
    services = Service.objects.all()
    context = {
        'services': services,
    }
    return render(request, 'services/service_list.html', context)

def service_detail(request, service_id):
    service = get_object_or_404(Service, id=service_id)
    context = {
        'service': service,
        'related_services': Service.objects.filter(category=service.category).exclude(id=service.id)[:3]
    }
    return render(request, 'services/service_detail.html', context)

@login_required
def dashboard(request):
    if not request.user.email_verified:
        messages.warning(request, 'Please verify your email address to access all features.')
    
    # Get filter period from request (default to 'all')
    filter_period = request.GET.get('period', 'all')
    
    # Get current date and calculate filter dates
    today = timezone.now().date()
    start_date = None
    
    if filter_period == 'week':
        start_date = today - timedelta(days=7)
    elif filter_period == 'month':
        start_date = today - timedelta(days=30)
    elif filter_period == 'quarter':
        start_date = today - timedelta(days=90)
    
    # Base query for tickets
    ticket_query = Ticket.objects.all()
    
    # Apply date filter if selected
    if start_date:
        ticket_query = ticket_query.filter(created_at__date__gte=start_date)
    
    # Calculate open tickets count
    open_tickets_count = ticket_query.exclude(status__in=['resolved', 'closed']).count()
    
    # Calculate resolved tickets today
    resolved_today = ticket_query.filter(
        status='resolved',
        resolved_at__date=today
    ).count()
    
    # Calculate average response time (first comment after ticket creation)
    avg_response_time_hours = 0
    tickets_with_comments = ticket_query.filter(comments__isnull=False).distinct()
    if tickets_with_comments.exists():
        total_hours = 0
        count = 0
        for ticket in tickets_with_comments:
            first_comment = ticket.comments.order_by('created_at').first()
            if first_comment:
                response_time = first_comment.created_at - ticket.created_at
                total_hours += response_time.total_seconds() / 3600  # Convert to hours
                count += 1
        if count > 0:
            avg_response_time_hours = round(total_hours / count, 1)
    
    # Format the average response time
    if avg_response_time_hours < 1:
        avg_response_time = f"{int(avg_response_time_hours * 60)}m"
    elif avg_response_time_hours >= 24:
        avg_response_time = f"{int(avg_response_time_hours / 24)}d"
    else:
        avg_response_time = f"{avg_response_time_hours}h"
    
    # Calculate overdue tickets
    overdue_tickets = ticket_query.filter(
        status__in=['new', 'assigned', 'in_progress', 'pending'],
        due_date__lt=timezone.now()
    ).count()
    
    # Calculate average resolution time
    avg_resolution_time_hours = 0
    resolved_tickets = ticket_query.filter(
        status='resolved',
        resolved_at__isnull=False
    )
    
    if resolved_tickets.exists():
        total_resolution_hours = 0
        for ticket in resolved_tickets:
            resolution_time = ticket.resolved_at - ticket.created_at
            total_resolution_hours += resolution_time.total_seconds() / 3600
        avg_resolution_time_hours = round(total_resolution_hours / resolved_tickets.count(), 1)
    
    # Format the average resolution time
    if avg_resolution_time_hours < 1:
        avg_resolution_time = f"{int(avg_resolution_time_hours * 60)}m"
    elif avg_resolution_time_hours >= 24:
        avg_resolution_time = f"{int(avg_resolution_time_hours / 24)}d"
    else:
        avg_resolution_time = f"{avg_resolution_time_hours}h"
    
    # Calculate tickets per day (daily average)
    daily_created_avg = 0
    if filter_period == 'all':
        # All time average
        first_ticket = Ticket.objects.order_by('created_at').first()
        if first_ticket:
            days_since_first_ticket = (today - first_ticket.created_at.date()).days + 1
            total_tickets = Ticket.objects.count()
            daily_created_avg = round(total_tickets / days_since_first_ticket, 1)
    else:
        # Average over the filtered period
        if start_date:
            days_in_period = (today - start_date).days + 1
            tickets_in_period = Ticket.objects.filter(created_at__date__gte=start_date).count()
            daily_created_avg = round(tickets_in_period / days_in_period, 1)
    
    # Calculate customer satisfaction rate (mock data for now)
    # In a real system, this would come from ticket feedback/ratings
    satisfaction_rate = "95%"
    
    # Get recent tickets (last 5)
    recent_tickets = ticket_query.order_by('-created_at')[:5]
    
    # Get chart data
    chart_data = {}
    
    # Ticket trend data based on filter period
    trend_dates = []
    trend_created = []
    trend_resolved = []
    
    if filter_period == 'week':
        # Last 7 days data
        for i in range(6, -1, -1):
            date = today - timedelta(days=i)
            trend_dates.append(date.strftime('%b %d'))
            trend_created.append(Ticket.objects.filter(created_at__date=date).count())
            trend_resolved.append(Ticket.objects.filter(resolved_at__date=date).count())
            
    elif filter_period == 'month':
        # Last 30 days data (grouped by weeks)
        for i in range(4):
            start_day = today - timedelta(days=(i+1)*7)
            end_day = today - timedelta(days=i*7)
            week_label = f"{start_day.strftime('%b %d')} - {end_day.strftime('%b %d')}"
            trend_dates.append(week_label)
            trend_created.append(Ticket.objects.filter(created_at__date__gt=start_day, created_at__date__lte=end_day).count())
            trend_resolved.append(Ticket.objects.filter(resolved_at__date__gt=start_day, resolved_at__date__lte=end_day).count())
        trend_dates.reverse()
        trend_created.reverse()
        trend_resolved.reverse()
            
    elif filter_period == 'quarter':
        # Last 90 days data (grouped by months)
        for i in range(3):
            month_start = today.replace(day=1) - timedelta(days=i*30)
            month_label = month_start.strftime('%B')
            trend_dates.append(month_label)
            month_created = Ticket.objects.filter(
                created_at__year=month_start.year,
                created_at__month=month_start.month
            ).count()
            month_resolved = Ticket.objects.filter(
                resolved_at__year=month_start.year,
                resolved_at__month=month_start.month,
                status='resolved'
            ).count()
            trend_created.append(month_created)
            trend_resolved.append(month_resolved)
        trend_dates.reverse()
        trend_created.reverse()
        trend_resolved.reverse()
            
    else:
        # Default: Last 7 days
        for i in range(6, -1, -1):
            date = today - timedelta(days=i)
            trend_dates.append(date.strftime('%b %d'))
            trend_created.append(Ticket.objects.filter(created_at__date=date).count())
            trend_resolved.append(Ticket.objects.filter(resolved_at__date=date).count())
    
    chart_data['daily'] = {
        'labels': trend_dates,
        'created': trend_created,
        'resolved': trend_resolved
    }
    
    # Status distribution
    status_labels = []
    status_counts = []
    
    for status_code, status_name in Ticket.Status.choices:
        status_labels.append(str(status_name))  # Convert proxy object to string
        status_counts.append(Ticket.objects.filter(status=status_code).count())
    
    chart_data['status'] = {
        'labels': status_labels,
        'counts': status_counts
    }
    
    # User-specific metrics for staff
    staff_metrics = None
    if request.user.is_staff:
        if hasattr(request.user, 'assigned_tickets'):
            assigned_count = request.user.assigned_tickets.count()
            resolved_count = request.user.assigned_tickets.filter(status='resolved').count()
            
            # Calculate resolution rate percentage
            resolution_rate = 0
            if assigned_count > 0:
                resolution_rate = int((resolved_count / assigned_count) * 100)
            
            # Calculate average handling time for this staff member
            avg_handling_time_hours = 0
            resolved_by_user = request.user.assigned_tickets.filter(
                status='resolved', 
                resolved_at__isnull=False
            )
            
            if resolved_by_user.exists():
                total_handling_hours = 0
                for ticket in resolved_by_user:
                    handling_time = ticket.resolved_at - ticket.created_at
                    total_handling_hours += handling_time.total_seconds() / 3600
                avg_handling_time_hours = round(total_handling_hours / resolved_by_user.count(), 1)
            
            # Format average handling time
            if avg_handling_time_hours < 1:
                avg_handling_time = f"{int(avg_handling_time_hours * 60)}m"
            elif avg_handling_time_hours >= 24:
                avg_handling_time = f"{int(avg_handling_time_hours / 24)}d"
            else:
                avg_handling_time = f"{avg_handling_time_hours}h"
            
            staff_metrics = {
                'assigned_count': assigned_count,
                'resolved_count': resolved_count,
                'resolution_rate': resolution_rate,
                'avg_handling_time': avg_handling_time
            }
    
    context = {
        'filter_period': filter_period,
        'open_tickets_count': open_tickets_count,
        'resolved_today': resolved_today,
        'avg_response_time': avg_response_time,
        'avg_resolution_time': avg_resolution_time,
        'overdue_tickets': overdue_tickets,
        'recent_tickets': recent_tickets,
        'chart_data': json.dumps(chart_data),
        'staff_metrics': staff_metrics,
        'daily_created_avg': daily_created_avg,
        'satisfaction_rate': satisfaction_rate,
    }
    return render(request, 'dashboard.html', context)

@login_required
def profile(request):
    # Get user tickets data
    user_tickets = Ticket.objects.filter(created_by=request.user)
    total_tickets = user_tickets.count()
    resolved_tickets = user_tickets.filter(status__in=['resolved', 'closed']).count()
    
    # Calculate average response time based on ticket comments
    avg_response_time_hours = 0
    if total_tickets > 0:
        # Get the first comment by a staff member for each ticket
        # This import is redundant as TicketComment is already imported at the top of the file
        # from apps.tickets.models import TicketComment
        
        # Get tickets with at least one comment
        tickets_with_comments = user_tickets.filter(comments__isnull=False).distinct()
        
        # Calculate average time for first response
        total_response_time = 0
        tickets_with_response = 0
        
        for ticket in tickets_with_comments:
            # Get the first comment by someone other than the ticket creator
            first_response = Comment.objects.filter(
                ticket=ticket,
                author__is_staff=True
            ).exclude(author=request.user).order_by('created_at').first()
            
            if first_response:
                # Calculate time difference between ticket creation and first response
                response_time = (first_response.created_at - ticket.created_at).total_seconds() / 3600  # hours
                total_response_time += response_time
                tickets_with_response += 1
        
        if tickets_with_response > 0:
            avg_response_time_hours = total_response_time / tickets_with_response
    
    # Format the average response time
    hours = int(avg_response_time_hours)
    minutes = int((avg_response_time_hours - hours) * 60)
    avg_response_time = f"{hours}h {minutes}m" if hours > 0 else f"{minutes}m"
    
    # Get recent activities (using ticket updates as activities)
    recent_activities = []
    
    # Get last 5 tickets created by the user
    recent_tickets = user_tickets.order_by('-created_at')[:5]
    for ticket in recent_tickets:
        # Add ticket creation activity
        recent_activities.append({
            'title': f"Created ticket #{ticket.id}: {ticket.title}",
            'description': f"Status: {ticket.get_status_display()}",
            'timestamp': ticket.created_at,
            'type': 'ticket_created'
        })
    
    # Get recent comments on the user's tickets
    from django.db.models import Q
    recent_comments = Comment.objects.filter(
        Q(ticket__in=user_tickets) & ~Q(author=request.user)
    ).order_by('-created_at')[:5]
    
    for comment in recent_comments:
        recent_activities.append({
            'title': f"New comment on ticket #{comment.ticket.id}",
            'description': f"From: {comment.author.get_full_name() or comment.author.username}",
            'timestamp': comment.created_at,
            'type': 'comment_received'
        })
    
    # Sort activities by timestamp
    recent_activities.sort(key=lambda x: x['timestamp'], reverse=True)
    recent_activities = recent_activities[:10]  # Limit to 10 most recent activities
    
    # Get ticket resolution rate
    resolution_rate = 0
    if total_tickets > 0:
        resolution_rate = (resolved_tickets / total_tickets) * 100
    
    # Calculate average ticket age for open tickets
    open_tickets = user_tickets.exclude(status__in=['resolved', 'closed'])
    avg_ticket_age_days = 0
    
    if open_tickets.exists():
        total_age = sum((timezone.now() - ticket.created_at).days for ticket in open_tickets)
        avg_ticket_age_days = total_age / open_tickets.count()
    
    context = {
        'total_tickets': total_tickets,
        'resolved_tickets': resolved_tickets,
        'open_tickets': total_tickets - resolved_tickets,
        'avg_response_time': avg_response_time,
        'recent_activities': recent_activities,
        'resolution_rate': round(resolution_rate, 1),
        'avg_ticket_age_days': round(avg_ticket_age_days, 1),
    }
    return render(request, 'users/profile.html', context)

@login_required
def settings(request):
    """
    Display user settings page. Retrieve settings from the database.
    """
    try:
        try:
            user_settings = request.user.settings
        except:
            # If settings don't exist, create them
            from apps.core.models import UserSettings
            user_settings = UserSettings.objects.create(user=request.user)
        
        # Load settings data from the user_settings model
        settings_data = {
            'notifications': user_settings.notifications,
            'preferences': user_settings.preferences,
            'appearance': user_settings.appearance,
            'privacy': user_settings.privacy,
            'system': user_settings.system if request.user.is_staff else {},
        }
        
        context = {
            'settings': settings_data,
            'available_timezones': ['UTC', 'US/Eastern', 'US/Pacific', 'Europe/London', 'Asia/Tokyo', 'Asia/Dubai', 'Europe/Paris', 'Africa/Cairo'],
            'available_colors': ['primary', 'success', 'info', 'warning', 'danger', 'secondary', 'dark'],
        }
        
        return render(request, 'users/settings.html', context)
    except Exception as e:
        messages.error(request, f"Error loading settings: {str(e)}")
        return redirect('core:dashboard')

@ensure_csrf_cookie
def register(request):
    """
    User registration view with improved CSRF handling and error reporting.
    """
    if request.method == 'POST':
        email = request.POST.get('email')
        password1 = request.POST.get('password1')
        password2 = request.POST.get('password2')
        first_name = request.POST.get('first_name')
        last_name = request.POST.get('last_name')
        terms = request.POST.get('terms')
        
        # Debug logging
        logger.info(f'Registration attempt for email: {email}')
        logger.info(f'Password length: {len(password1) if password1 else 0}')
        logger.info(f'Has digit: {any(char.isdigit() for char in password1) if password1 else False}')
        logger.info(f'Has letter: {any(char.isalpha() for char in password1) if password1 else False}')
        logger.info(f'Terms accepted: {bool(terms)}')
        
        # Validate required fields
        if not all([email, password1, password2, first_name, last_name]):
            messages.error(request, 'All fields are required.')
            return render(request, 'users/register.html')
        
        # Validate terms acceptance
        if not terms:
            messages.error(request, 'You must accept the Terms and Conditions.')
            return render(request, 'users/register.html')
        
        # Validate passwords
        if password1 != password2:
            messages.error(request, 'Passwords do not match.')
            return render(request, 'users/register.html')
        
        # Validate password strength
        if len(password1) < 8:
            logger.warning(f'Password too short: {len(password1)} characters')
            messages.error(request, 'Password must be at least 8 characters long.')
            return render(request, 'users/register.html')
        
        if not any(char.isdigit() for char in password1):
            logger.warning('Password missing number')
            messages.error(request, 'Password must contain at least one number.')
            return render(request, 'users/register.html')
            
        if not any(char.isalpha() for char in password1):
            logger.warning('Password missing letter')
            messages.error(request, 'Password must contain at least one letter.')
            return render(request, 'users/register.html')
            
        # Check if email is already registered
        if User.objects.filter(email=email).exists():
            messages.error(request, 'Email already registered.')
            return render(request, 'users/register.html')
        
        try:
            # Create user
            username = email.split('@')[0]
            base_username = username
            counter = 1
            
            # Ensure unique username
            while User.objects.filter(username=username).exists():
                username = f"{base_username}{counter}"
                counter += 1
            
            user = User.objects.create_user(
                username=username,
                email=email,
                password=password1,
                first_name=first_name,
                last_name=last_name,
                is_active=True
            )
            
            # Create user profile - update to handle duplicates
            try:
                # Check if profile already exists
                profile, created = Profile.objects.get_or_create(
                    user=user,
                    defaults={
                        'phone': '',
                        'address': '',
                        'bio': '',
                        'notification_preferences': {}
                    }
                )
                if not created:
                    logger.info(f"Profile already existed for user {user.id}, using existing profile")
            except Exception as profile_error:
                logger.error(f"Error creating profile: {str(profile_error)}")
                # Continue with registration even if profile creation fails
                # The profile can be created later
            
            # Send verification email
            user.send_verification_email(request)
            
            messages.success(request, 'Registration successful! Please check your email to verify your account.')
            return render(request, 'users/email_verification_sent.html', {'email': email})
            
        except Exception as e:
            logger.error(f'Error during registration: {str(e)}')
            messages.error(request, 'An error occurred during registration. Please try again.')
            return render(request, 'users/register.html')
            
    return render(request, 'users/register.html')

def verify_email(request, uidb64, token):
    try:
        uid = force_str(urlsafe_base64_decode(uidb64))
        user = User.objects.get(pk=uid)
    except (TypeError, ValueError, OverflowError, User.DoesNotExist, ValidationError):
        user = None
    
    if user is not None and default_token_generator.check_token(user, token):
        if not user.email_verified:
            user.email_verified = True
            user.email_verification_token = ''
            user.save()
            messages.success(request, 'Email verified successfully!')
        return render(request, 'users/email_verification_success.html')
    else:
        messages.error(request, 'The verification link is invalid or has expired.')
        return redirect('core:login')

@require_POST
def resend_verification(request):
    email = request.POST.get('email')
    try:
        user = User.objects.get(email=email, email_verified=False)
        user.send_verification_email(request)
        messages.success(request, 'Verification email sent successfully!')
    except User.DoesNotExist:
        messages.error(request, 'Invalid email address.')
    
    return render(request, 'users/email_verification_sent.html', {'email': email})

def login_view(request):
    """
    Handle user login and redirect to appropriate dashboard.
    """
    if request.method == 'POST':
        email = request.POST.get('email')
        password = request.POST.get('password')
        remember_me = request.POST.get('remember_me')
        
        user = authenticate(request, email=email, password=password)
        
        if user is not None:
            # Check if email is verified
            if not user.email_verified:
                return render(request, 'users/email_verification_sent.html', {'email': email})
                
            login(request, user)
            
            # Set session expiry based on remember me checkbox
            if remember_me:
                # Keep session for 2 weeks
                request.session.set_expiry(1209600)
            else:
                request.session.set_expiry(0)  # Session expires when browser closes
            
            # Log user role and authentication status
            logger.info(f"User logged in - Email: {email}, Role: {user.role}, Is Authenticated: {user.is_authenticated}")
            
            # Get next URL if it exists
            next_url = request.GET.get('next')
            if next_url:
                return redirect(next_url)
            
            # Redirect to appropriate dashboard based on role
            if user.role == 'technician':
                return redirect('core:technician_dashboard')
            else:
                return redirect('core:dashboard')
        else:
            messages.error(request, 'Invalid email or password')
            logger.warning(f"Failed login attempt - Email: {email}")
    
    return render(request, 'users/login.html')

def logout_view(request):
    logout(request)
    return redirect('core:login')

@login_required
@require_POST
def update_profile(request):
    """
    Update user profile information.
    """
    try:
        # Get the form data
        first_name = request.POST.get('first_name')
        last_name = request.POST.get('last_name')
        phone_number = request.POST.get('phone_number', '')
        department = request.POST.get('department', '')
        
        # Update user data
        user = request.user
        user.first_name = first_name
        user.last_name = last_name
        
        # Update phone field (which is correct on User model)
        user.phone = phone_number
            
        # Save the user first
        user.save()
        
        # Update Profile model if it exists
        try:
            profile = user.profile
            
            # Update the profile fields
            profile.department = department
            
            # If phone is also on the profile model, update it there too for consistency
            if hasattr(profile, 'phone'):
                profile.phone = phone_number
                
            # Save the profile
            profile.save()
        except Exception as profile_error:
            # Log the error but continue
            logger.error(f"Error updating profile: {str(profile_error)}")
        
        return JsonResponse({
            'success': True, 
            'message': 'Profile updated successfully',
            'updated_fields': {
                'first_name': first_name,
                'last_name': last_name,
                'phone_number': phone_number,
                'department': department
            }
        })
    except Exception as e:
        return JsonResponse({'success': False, 'message': f'Error updating profile: {str(e)}'})

@login_required
@require_POST
def update_profile_picture(request):
    """
    Update user profile picture
    """
    try:
        # Check if a file was uploaded
        if 'profile_picture' not in request.FILES:
            return JsonResponse({
                'success': False,
                'message': 'No image file was uploaded'
            })
        
        image_file = request.FILES['profile_picture']
        
        # Validate file type
        valid_types = ['image/jpeg', 'image/png', 'image/gif']
        if image_file.content_type not in valid_types:
            return JsonResponse({
                'success': False,
                'message': 'Invalid file type. Please upload a JPEG, PNG or GIF image.'
            })
        
        # Validate file size (max 5MB)
        max_size = 5 * 1024 * 1024  # 5MB
        if image_file.size > max_size:
            return JsonResponse({
                'success': False,
                'message': 'File size exceeds the 5MB limit'
            })
        
        # Get user
        user = request.user
        
        # Save to User.avatar field which is the correct field based on the models
        if hasattr(user, 'avatar'):
            # Delete old avatar if it exists
            if user.avatar:
                try:
                    storage = user.avatar.storage
                    if storage.exists(user.avatar.name):
                        storage.delete(user.avatar.name)
                except Exception as e:
                    logger.error(f"Error deleting old avatar: {str(e)}")
            
            # Save new avatar
            user.avatar = image_file
            user.save()
            
            return JsonResponse({
                'success': True,
                'message': 'Profile picture updated successfully'
            })
        else:
            return JsonResponse({
                'success': False,
                'message': 'Profile picture could not be saved - avatar field not found'
            })
        
    except Exception as e:
        logger.error(f"Error updating profile picture: {str(e)}")
        return JsonResponse({
            'success': False,
            'message': f'Error updating profile picture: {str(e)}'
        })

@login_required
@require_POST
def change_password(request):
    """
    Change user password via AJAX
    """
    try:
        # Get form data
        current_password = request.POST.get('current_password')
        new_password1 = request.POST.get('new_password1')
        new_password2 = request.POST.get('new_password2')
        
        # Validate input
        if not current_password or not new_password1 or not new_password2:
            return JsonResponse({
                'success': False, 
                'message': 'All password fields are required'
            })
        
        # Check if new passwords match
        if new_password1 != new_password2:
            return JsonResponse({
                'success': False, 
                'message': 'New passwords do not match'
            })
        
        # Verify current password
        user = request.user
        if not user.check_password(current_password):
            return JsonResponse({
                'success': False, 
                'message': 'Current password is incorrect'
            })
        
        # Basic password strength check
        if len(new_password1) < 8:
            return JsonResponse({
                'success': False, 
                'message': 'Password must be at least 8 characters long'
            })
        
        # Set new password
        user.set_password(new_password1)
        user.save()
        
        # Update session auth hash to prevent user from being logged out
        update_session_auth_hash(request, user)
        
        return JsonResponse({
            'success': True, 
            'message': 'Password changed successfully'
        })
    
    except Exception as e:
        return JsonResponse({
            'success': False, 
            'message': f'Error changing password: {str(e)}'
        })

@login_required
@require_POST
def update_notification_settings(request):
    """
    Update user notification settings.
    """
    try:
        # Try to parse JSON data from request body
        try:
            data = json.loads(request.body.decode('utf-8'))
        except:
            # Fall back to POST data if JSON parsing fails
            data = request.POST
            
        user_settings = request.user.settings
        
        # Update each notification setting
        notifications = user_settings.notifications
        notifications['new_ticket'] = data.get('new_ticket', False)
        notifications['ticket_update'] = data.get('ticket_update', False)
        notifications['ticket_resolved'] = data.get('ticket_resolved', False)
        notifications['browser_notifications'] = data.get('browser_notifications', False)
        notifications['sound_notifications'] = data.get('sound_notifications', False)
        
        user_settings.notifications = notifications
        user_settings.save()
        
        return JsonResponse({'success': True, 'message': 'Notification settings updated'})
    except Exception as e:
        return JsonResponse({'success': False, 'message': f'Error updating settings: {str(e)}'})

@login_required
@require_POST
def update_preferences(request):
    """
    Update user preferences.
    """
    try:
        # Try to parse JSON data from request body
        try:
            data = json.loads(request.body.decode('utf-8'))
        except:
            # Fall back to POST data if JSON parsing fails
            data = request.POST
            
        user_settings = request.user.settings
        
        # Update preference settings
        preferences = user_settings.preferences
        preferences['default_view'] = data.get('default_view', 'tickets')
        preferences['items_per_page'] = int(data.get('items_per_page', 25))
        preferences['timezone'] = data.get('timezone', 'UTC')
        
        user_settings.preferences = preferences
        user_settings.save()
        
        return JsonResponse({'success': True, 'message': 'Preferences updated'})
    except Exception as e:
        return JsonResponse({'success': False, 'message': f'Error updating preferences: {str(e)}'})

@login_required
@require_POST
def update_privacy(request):
    """
    Update user privacy settings.
    """
    try:
        # Try to parse JSON data from request body
        try:
            data = json.loads(request.body.decode('utf-8'))
        except:
            # Fall back to POST data if JSON parsing fails
            data = request.POST
            
        user_settings = request.user.settings
        
        # Update privacy settings
        privacy = user_settings.privacy
        privacy['show_online_status'] = data.get('show_online_status', False)
        privacy['show_activity'] = data.get('show_activity', False)
        privacy['show_email'] = data.get('show_email', False)
        
        user_settings.privacy = privacy
        user_settings.save()
        
        return JsonResponse({'success': True, 'message': 'Privacy settings updated'})
    except Exception as e:
        return JsonResponse({'success': False, 'message': f'Error updating privacy settings: {str(e)}'})

@login_required
@require_POST
def update_system_settings(request):
    """
    Update system settings (admin only).
    """
    if not request.user.is_staff:
        return JsonResponse({'success': False, 'message': 'Permission denied'}, status=403)
    
    try:
        # Try to parse JSON data from request body
        try:
            data = json.loads(request.body.decode('utf-8'))
        except:
            # Fall back to POST data if JSON parsing fails
            data = request.POST
            
        user_settings = request.user.settings
        
        # Update system settings
        system = user_settings.system or {}
        system['auto_assign'] = data.get('auto_assign', False)
        system['default_due_date'] = int(data.get('default_due_date', 3))
        system['email_enabled'] = data.get('email_enabled', False)
        system['system_email'] = data.get('system_email', '')
        
        user_settings.system = system
        user_settings.save()
        
        return JsonResponse({'success': True, 'message': 'System settings updated'})
    except Exception as e:
        return JsonResponse({'success': False, 'message': f'Error updating system settings: {str(e)}'})

@login_required
@user_passes_test(is_technician)
def toggle_availability(request):
    """Toggle technician availability status via AJAX"""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            is_available = data.get('available', False)
            
            # Get or create technician profile
            profile, created = TechnicianProfile.objects.get_or_create(user=request.user)
            profile.is_available = is_available
            profile.save()
            
            return JsonResponse({
                'status': 'success',
                'available': is_available
            })
        except Exception as e:
            return JsonResponse({
                'status': 'error',
                'message': str(e)
            }, status=400)
    return JsonResponse({
        'status': 'error',
        'message': 'Method not allowed'
    }, status=405)

@login_required
def tickets(request):
    """
    Display user's support tickets and handle new ticket creation.
    """
    # Add extensive logging
    logger.info("=== Tickets View ===")
    logger.info(f"User authenticated: {request.user.is_authenticated}")
    if request.user.is_authenticated:
        logger.info(f"User email: {request.user.email}")
        logger.info(f"User ID: {request.user.id}")

    if not request.user.is_authenticated:
        messages.error(request, 'Please log in to view your tickets.')
        return redirect('core:login')

    # Get user's tickets with related service info
    user_tickets = Ticket.objects.select_related('service', 'created_by').filter(
        created_by=request.user
    ).order_by('-created_at')
    
    # Log detailed ticket information
    logger.info(f"Total tickets found: {user_tickets.count()}")
    for ticket in user_tickets:
        logger.info(
            f"Ticket #{ticket.id}: {ticket.title}\n"
            f"  - Status: {ticket.status}\n"
            f"  - Service: {ticket.service.name if ticket.service else 'No service'}\n"
            f"  - Created: {ticket.created_at}\n"
            f"  - Priority: {ticket.priority}"
        )
    
    # Calculate counts for statistics cards
    resolved_tickets_count = user_tickets.filter(status='resolved').count()
    in_progress_tickets_count = user_tickets.filter(status='in_progress').count()
    new_tickets_count = user_tickets.filter(status='new').count()
    
    services = Service.objects.filter(is_active=True)
    
    # Log tickets and services for debugging
    logger.info("=== Available Services ===")
    for service in services:
        logger.info(f"Service: {service.name} (ID: {service.id})")

    context = {
        'tickets': user_tickets,
        'services': services,
        'resolved_tickets_count': resolved_tickets_count,
        'in_progress_tickets_count': in_progress_tickets_count,
        'new_tickets_count': new_tickets_count,
        'total_tickets': user_tickets.count(),
    }

    # Log the full context for debugging
    logger.info("=== Template Context ===")
    logger.info(f"Total tickets: {context['total_tickets']}")
    logger.info(f"Services count: {len(context['services'])}")
    logger.info(f"Resolved tickets: {context['resolved_tickets_count']}")
    logger.info(f"In progress tickets: {context['in_progress_tickets_count']}")
    logger.info(f"New tickets: {context['new_tickets_count']}")
    
    return render(request, 'support/tickets.html', context)

@login_required
def create_ticket(request):
    """
    Handle ticket creation via AJAX, regular form submission, or display the form.
    """
    # Get available services
    services = Service.objects.all()
    
    # Handle GET request - show the form
    if request.method == 'GET':
        # Pre-fill service if provided in query params
        initial_service_id = request.GET.get('service')
        initial_service = None
        if initial_service_id:
            try:
                initial_service = Service.objects.get(id=initial_service_id)
            except Service.DoesNotExist:
                pass
        
        context = {
            'services': services,
            'initial_service': initial_service,
            'priorities': Ticket.Priority.choices
        }
        return render(request, 'support/create_ticket.html', context)
    
    # Handle POST request
    try:
        # Get form data
        service_id = request.POST.get('service')
        subject = request.POST.get('subject')
        description = request.POST.get('description')
        priority = request.POST.get('priority', 'normal')
        
        # Validate required fields
        if not all([service_id, subject, description]):
            raise ValidationError('Please fill in all required fields')
        
        # Create ticket
        ticket = Ticket.objects.create(
            created_by=request.user,
            service_id=service_id,
            title=subject,
            description=description,
            priority=priority,
            status='new'
        )
        
        # Handle file attachments - manually process the files list
        if 'attachments' in request.FILES:
            files = request.FILES.getlist('attachments')
            for file in files:
                if file.size > 5 * 1024 * 1024:  # 5MB limit
                    raise ValidationError(f'File {file.name} exceeds 5MB size limit')
                TicketAttachment.objects.create(ticket=ticket, file=file)
        
        # Return success response
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({
                'success': True,
                'message': 'Ticket created successfully',
                'ticket_id': ticket.id
            })
        
        messages.success(request, 'Ticket created successfully')
        return redirect('core:tickets')
        
    except ValidationError as e:
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'success': False, 'message': str(e)}, status=400)
        
        messages.error(request, str(e))
        return redirect('core:ticket_create')
        
    except Exception as e:
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'success': False, 'message': 'An error occurred while creating the ticket'}, status=500)
        
        messages.error(request, 'An error occurred while creating the ticket')
        return redirect('core:ticket_create')

@login_required
def ticket_detail(request, ticket_id):
    """
    Display ticket details and handle ticket updates.
    """
    ticket = get_object_or_404(Ticket, id=ticket_id)
    
    # Check if user has permission to view this ticket
    if ticket.created_by != request.user and not request.user.is_staff:
        messages.error(request, 'You do not have permission to view this ticket.')
        return redirect('core:tickets')
    
    # Get ticket attachments
    attachments = TicketAttachment.objects.filter(ticket=ticket)
    
    # Get ticket history/updates
    updates = ticket.updates.all().order_by('-created_at') if hasattr(ticket, 'updates') else []
    
    context = {
        'ticket': ticket,
        'attachments': attachments,
        'updates': updates,
        'can_update': request.user.is_staff or ticket.status not in ['closed', 'resolved'],
        'statuses': Ticket.Status.choices,
        'priorities': Ticket.Priority.choices,
    }
    
    return render(request, 'tickets/ticket_detail.html', context)

def contact(request):
    if request.method == 'POST':
        name = request.POST.get('name')
        email = request.POST.get('email')
        subject = request.POST.get('subject')
        message = request.POST.get('message')
        
        # Here you would typically send an email or create a contact entry
        # For now, we'll just show a success message
        messages.success(request, 'Thank you for your message! We will get back to you soon.')
        return redirect('core:contact')
    
    return render(request, 'contact.html')

def faq(request):
    """
    Display the FAQ page with categorized questions and answers.
    """
    technical_faqs = FAQ.objects.filter(category='technical', is_published=True)
    billing_faqs = FAQ.objects.filter(category='billing', is_published=True)
    services_faqs = FAQ.objects.filter(category='services', is_published=True)
    
    context = {
        'technical_faqs': technical_faqs,
        'billing_faqs': billing_faqs,
        'services_faqs': services_faqs,
    }
    
    return render(request, 'support/faq.html', context)

def service_request(request):
    """
    Display the service request form and handle form submissions.
    """
    if request.method == 'POST':
        # Handle form submission
        try:
            # Process the form data and files
            data = request.POST
            files = request.FILES
            
            # Create service request record (implement your model logic here)
            
            # Return success response for AJAX request
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'success': True,
                    'message': 'Your service request has been submitted successfully. We will contact you shortly.'
                })
            
            # Redirect to success page for regular form submission
            messages.success(request, 'Your service request has been submitted successfully. We will contact you shortly.')
            return redirect('core:service_request')
            
        except Exception as e:
            # Return error response for AJAX request
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'success': False,
                    'message': 'An error occurred while submitting your request. Please try again.'
                })
            
            # Show error message for regular form submission
            messages.error(request, 'An error occurred while submitting your request. Please try again.')
    
    # Get list of services for the form
    services = Service.objects.all()
    
    context = {
        'services': services,
    }
    
    return render(request, 'services/service_request.html', context)

@login_required
def submit_service_request(request):
    """
    Handle service request submission.
    """
    if request.method != 'POST':
        return JsonResponse({'success': False, 'message': 'Invalid request method'}, status=405)
    
    try:
        # Get form data
        service_id = request.POST.get('service_type')
        priority = request.POST.get('priority', 'normal')
        description = request.POST.get('description')
        contact_method = request.POST.get('contact_method', 'email')
        preferred_time = request.POST.get('preferred_time')
        
        # Validate required fields
        if not all([service_id, description]):
            raise ValidationError('Please fill in all required fields')
        
        # Create ticket for the service request
        ticket = Ticket.objects.create(
            created_by=request.user,
            service_id=service_id,
            title=f"Service Request - {Service.objects.get(id=service_id).name}",
            description=description,
            priority=priority,
            status='new',
            contact_method=contact_method,
            preferred_contact_time=preferred_time if preferred_time else None
        )
        
        # Handle file attachments
        files = request.FILES.getlist('attachments')
        for file in files:
            if file.size > 5 * 1024 * 1024:  # 5MB limit
                raise ValidationError(f'File {file.name} exceeds 5MB size limit')
            TicketAttachment.objects.create(ticket=ticket, file=file)
        
        # Send email notification to staff
        try:
            subject = f'New Service Request - {ticket.title}'
            message = f'''
            A new service request has been submitted:
            
            Service: {ticket.service.name}
            Priority: {ticket.priority}
            Description: {ticket.description}
            Contact Method: {ticket.contact_method}
            Preferred Time: {ticket.preferred_contact_time or 'Not specified'}
            
            View ticket: http://{request.get_host()}/tickets/{ticket.id}/
            '''
            send_mail(
                subject,
                message,
                settings.DEFAULT_FROM_EMAIL,
                [admin[1] for admin in settings.ADMINS],
                fail_silently=True,
            )
        except Exception as e:
            # Log the error but don't fail the request
            logger.error(f'Failed to send email notification: {str(e)}')
        
        # Return success response
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({
                'success': True,
                'message': 'Service request submitted successfully',
                'ticket_id': ticket.id
            })
        
        messages.success(request, 'Service request submitted successfully')
        return redirect('core:tickets')
        
    except ValidationError as e:
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'success': False, 'message': str(e)}, status=400)
        
        messages.error(request, str(e))
        return redirect('core:service_request')
        
    except Exception as e:
        logger.error(f'Error submitting service request: {str(e)}')
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'success': False, 'message': 'An error occurred while submitting your request'}, status=500)
        
        messages.error(request, 'An error occurred while submitting your request')
        return redirect('core:service_request')

@login_required
@require_POST
def reset_notification_settings(request):
    """
    Reset notification settings to default values.
    """
    try:
        user_settings = request.user.settings
        user_settings.notifications = user_settings.get_default_notifications()
        user_settings.save()
        
        return JsonResponse({'success': True, 'message': 'Notification settings reset to defaults'})
    except Exception as e:
        return JsonResponse({'success': False, 'message': f'Error resetting settings: {str(e)}'})

@login_required
@require_POST
def reset_preferences(request):
    """
    Reset preferences to default values.
    """
    try:
        user_settings = request.user.settings
        user_settings.preferences = user_settings.get_default_preferences()
        user_settings.save()
        
        return JsonResponse({'success': True, 'message': 'Preferences reset to defaults'})
    except Exception as e:
        return JsonResponse({'success': False, 'message': f'Error resetting preferences: {str(e)}'})

@login_required
@require_POST
def reset_privacy(request):
    """
    Reset privacy settings to default values.
    """
    try:
        user_settings = request.user.settings
        user_settings.privacy = user_settings.get_default_privacy()
        user_settings.save()
        
        return JsonResponse({'success': True, 'message': 'Privacy settings reset to defaults'})
    except Exception as e:
        return JsonResponse({'success': False, 'message': f'Error resetting privacy settings: {str(e)}'})

@login_required
@require_POST
def reset_system_settings(request):
    """
    Reset system settings to default values (admin only).
    """
    if not request.user.is_staff:
        return JsonResponse({'success': False, 'message': 'Permission denied'}, status=403)
    
    try:
        user_settings = request.user.settings
        user_settings.system = user_settings.get_default_system()
        user_settings.save()
        
        return JsonResponse({'success': True, 'message': 'System settings reset to defaults'})
    except Exception as e:
        return JsonResponse({'success': False, 'message': f'Error resetting system settings: {str(e)}'})

@login_required
def update_ticket(request, ticket_id):
    """
    Update an existing ticket.
    """
    ticket = get_object_or_404(Ticket, id=ticket_id)
    
    # Check if user has permission to update this ticket
    if ticket.created_by != request.user and not request.user.is_staff:
        messages.error(request, 'You do not have permission to update this ticket.')
        return redirect('core:tickets')
    
    # Check if ticket is closed
    if ticket.status == 'closed':
        messages.error(request, 'This ticket is closed and cannot be updated.')
        return redirect('core:ticket_detail', ticket_id=ticket_id)
    
    if request.method == 'POST':
        try:
            # Get form data
            subject = request.POST.get('subject')
            description = request.POST.get('description')
            priority = request.POST.get('priority')
            status = request.POST.get('status')
            
            # Update ticket
            if subject:
                ticket.title = subject
            if description:
                ticket.description = description
            if priority:
                ticket.priority = priority
            if status and (request.user.is_staff or status != 'closed'):
                ticket.status = status
            
            ticket.save()
            
            # Handle file attachments
            if 'attachments' in request.FILES:
                files = request.FILES.getlist('attachments')
                for file in files:
                    if file.size > 5 * 1024 * 1024:  # 5MB limit
                        raise ValidationError(f'File {file.name} exceeds 5MB size limit')
                    TicketAttachment.objects.create(ticket=ticket, file=file)
            
            # Return success response for AJAX requests
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'success': True,
                    'message': 'Ticket updated successfully',
                    'ticket_id': ticket.id
                })
            
            messages.success(request, 'Ticket updated successfully')
            return redirect('core:ticket_detail', ticket_id=ticket_id)
            
        except ValidationError as e:
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({'success': False, 'message': str(e)}, status=400)
            
            messages.error(request, str(e))
            return redirect('core:ticket_detail', ticket_id=ticket_id)
            
        except Exception as e:
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({'success': False, 'message': 'An error occurred while updating the ticket'}, status=500)
            
            messages.error(request, 'An error occurred while updating the ticket')
            return redirect('core:ticket_detail', ticket_id=ticket_id)
    
    # For GET requests, redirect to ticket detail page
    return redirect('core:ticket_detail', ticket_id=ticket_id)

@login_required
def technician_dashboard(request):
    """
    Display the technician dashboard with assigned tickets, SLA alerts, team performance,
    and knowledge base articles.
    """
    # Log authentication status and role
    logger.info(f"Technician Dashboard Access - User: {request.user.email}, "
               f"Role: {request.user.role}, "
               f"Is Authenticated: {request.user.is_authenticated}")

    # Ensure user is a technician
    if not is_technician(request.user) and not request.user.is_superuser:
        logger.warning(f"Unauthorized access attempt to technician dashboard - "
                      f"User: {request.user.email}, Role: {request.user.role}")
        messages.error(request, "Access denied. You must be a technician to view this page.")
        return redirect('core:dashboard')
    
    # Get filter period
    filter_period = request.GET.get('period', 'all')
    
    # Determine date range based on filter period
    now = timezone.now()
    filter_date = None
    
    if filter_period == 'today':
        filter_date = now.date()
    elif filter_period == 'week':
        filter_date = now - timedelta(days=7)
    elif filter_period == 'month':
        filter_date = now - timedelta(days=30)
    elif filter_period == 'quarter':
        filter_date = now - timedelta(days=90)
    
    # Get tickets assigned to this technician
    tickets_query = Ticket.objects.filter(assigned_to=request.user)
    
    # Apply date filter if specified
    if filter_date:
        if isinstance(filter_date, datetime.date):
            # For "today", filter by date
            tickets_query = tickets_query.filter(created_at__date=filter_date)
        else:
            # For other periods, filter by range
            tickets_query = tickets_query.filter(created_at__gte=filter_date)
    
    # Get assigned tickets with pagination
    paginator = Paginator(tickets_query.order_by('-created_at'), 10)
    page_number = request.GET.get('page', 1)
    assigned_tickets = paginator.get_page(page_number)
    
    # Calculate metrics
    assigned_tickets_count = tickets_query.count()
    resolved_today = tickets_query.filter(
        status='resolved',
        updated_at__date=now.date()
    ).count()
    
    # Calculate average response time
    avg_response_time_hours = 0
    tickets_with_response = 0
    
    for ticket in tickets_query.filter(status__in=['in_progress', 'resolved', 'closed']):
        # Find the first response by the technician
        first_response = Comment.objects.filter(
            ticket=ticket,
            author=request.user
        ).order_by('created_at').first()
        
        if first_response:
            # Calculate time difference
            response_time = (first_response.created_at - ticket.created_at).total_seconds() / 3600  # hours
            avg_response_time_hours += response_time
            tickets_with_response += 1
    
    if tickets_with_response > 0:
        avg_response_time_hours = avg_response_time_hours / tickets_with_response
        
    # Format the average response time
    hours = int(avg_response_time_hours)
    minutes = int((avg_response_time_hours - hours) * 60)
    avg_response_time = f"{hours}h {minutes}m" if hours > 0 else f"{minutes}m"
    
    # Calculate resolution rate
    all_time_assigned = Ticket.objects.filter(assigned_to=request.user).count()
    all_time_resolved = Ticket.objects.filter(
        assigned_to=request.user,
        status__in=['resolved', 'closed']
    ).count()
    
    resolution_rate = 0
    if all_time_assigned > 0:
        resolution_rate = int((all_time_resolved / all_time_assigned) * 100)
    
    # Get SLA alerts
    sla_alerts = []
    
    # Get tickets that are at risk of breaching SLA
    at_risk_tickets = tickets_query.filter(status__in=['new', 'in_progress'])
    
    for ticket in at_risk_tickets:
        # Calculate SLA based on priority
        sla_hours = 24  # Default SLA
        if ticket.priority == 'high':
            sla_hours = 4
        elif ticket.priority == 'medium':
            sla_hours = 8
        elif ticket.priority == 'low':
            sla_hours = 24
        
        # Calculate hours since creation
        hours_since_creation = (now - ticket.created_at).total_seconds() / 3600
        
        # Check if SLA is breached or at risk
        if hours_since_creation >= sla_hours:
            sla_alerts.append({
                'ticket_id': ticket.id,
                'title': ticket.title,
                'severity': 'high',
                'message': f'SLA breached: Ticket has been open for {int(hours_since_creation)} hours (SLA: {sla_hours} hours)'
            })
        elif hours_since_creation >= (sla_hours * 0.75):
            sla_alerts.append({
                'ticket_id': ticket.id,
                'title': ticket.title,
                'severity': 'medium',
                'message': f'SLA at risk: Ticket has been open for {int(hours_since_creation)} hours (SLA: {sla_hours} hours)'
            })
    
    # Sort alerts by severity (high first)
    sla_alerts.sort(key=lambda x: 0 if x['severity'] == 'high' else 1)
    
    # Get team performance data
    team_performance = []
    
    # Get technicians (users with role='technician')
    technicians = User.objects.filter(role='technician')
    
    for technician in technicians:
        # Skip if this is the current user
        if technician.id == request.user.id:
            continue
            
        assigned_count = Ticket.objects.filter(assigned_to=technician).count()
        resolved_count = Ticket.objects.filter(
            assigned_to=technician,
            status__in=['resolved', 'closed']
        ).count()
        
        # Calculate performance score (simple metric based on resolution rate)
        performance_score = 0
        if assigned_count > 0:
            performance_score = int((resolved_count / assigned_count) * 100)
        
        # Determine performance level
        performance_level = 'below-average'
        if performance_score >= 90:
            performance_level = 'excellent'
        elif performance_score >= 75:
            performance_level = 'good'
        elif performance_score >= 50:
            performance_level = 'average'
        
        # Calculate average response time for technician
        tech_avg_response_hours = 0
        tech_tickets_with_response = 0
        
        for ticket in Ticket.objects.filter(assigned_to=technician):
            first_response = Comment.objects.filter(
                ticket=ticket,
                author=technician
            ).order_by('created_at').first()
            
            if first_response:
                tech_response_time = (first_response.created_at - ticket.created_at).total_seconds() / 3600
                tech_avg_response_hours += tech_response_time
                tech_tickets_with_response += 1
        
        if tech_tickets_with_response > 0:
            tech_avg_response_hours = tech_avg_response_hours / tech_tickets_with_response
            
        # Format the technician's average response time
        tech_hours = int(tech_avg_response_hours)
        tech_minutes = int((tech_avg_response_hours - tech_hours) * 60)
        tech_avg_response = f"{tech_hours}h {tech_minutes}m" if tech_hours > 0 else f"{tech_minutes}m"
        
        # Add technician performance data
        team_performance.append({
            'name': technician.get_full_name() or technician.username,
            'initials': technician.get_initials(),
            'avatar': technician.avatar.url if hasattr(technician, 'avatar') and technician.avatar else None,
            'assigned': assigned_count,
            'resolved': resolved_count,
            'avg_response': tech_avg_response,
            'performance_score': performance_score,
            'performance_level': performance_level
        })
    
    # Sort by performance score (highest first)
    team_performance.sort(key=lambda x: x['performance_score'], reverse=True)
    
    # Get recent knowledge base articles
    # This assumes you have a KnowledgeBaseArticle model - adjust as needed
    try:
        from apps.kb.models import KnowledgeBaseArticle
        recent_kb_articles = KnowledgeBaseArticle.objects.filter(
            is_published=True
        ).order_by('-created_at')[:5]
    except:
        # If the KB module doesn't exist yet, use empty list
        recent_kb_articles = []
    
    # Prepare context
    context = {
        'filter_period': filter_period,
        'assigned_tickets': assigned_tickets,
        'assigned_tickets_count': assigned_tickets_count,
        'resolved_today': resolved_today,
        'avg_response_time': avg_response_time,
        'resolution_rate': resolution_rate,
        'sla_alerts': sla_alerts,
        'team_performance': team_performance,
        'recent_kb_articles': recent_kb_articles,
    }
    
    return render(request, 'technician/dashboard.html', context)

@login_required
def technician_tickets(request):
    # Log authentication status and role
    logger.info(f"Technician Tickets Access - User: {request.user.email}, "
               f"Role: {request.user.role}, "
               f"Is Authenticated: {request.user.is_authenticated}")

    # Check if user is technician
    if not is_technician(request.user) and not request.user.is_superuser:
        logger.warning(f"Unauthorized access attempt to technician tickets - "
                      f"User: {request.user.email}, Role: {request.user.role}")
        messages.error(request, "Access denied. You must be a technician to view tickets.")
        return redirect('core:dashboard')

    # Get all tickets with related data
    tickets = Ticket.objects.select_related(
        'service', 'created_by', 'assigned_to'
    ).order_by('-created_at')
    
    # Apply filters
    status = request.GET.get('status')
    priority = request.GET.get('priority')
    assigned = request.GET.get('assigned')
    
    if status:
        tickets = tickets.filter(status=status)
    if priority:
        tickets = tickets.filter(priority=priority)
    if assigned:
        if assigned == 'me':
            tickets = tickets.filter(assigned_to=request.user)
        elif assigned == 'unassigned':
            tickets = tickets.filter(assigned_to=None)
    
    # Add ticket statistics
    stats = {
        'total': tickets.count(),
        'new': tickets.filter(status='new').count(),
        'in_progress': tickets.filter(status='in_progress').count(),
        'resolved': tickets.filter(status='resolved').count(),
    }
    
    context = {
        'tickets': tickets,
        'stats': stats,
        'status_choices': Ticket.Status.choices,
        'priority_choices': Ticket.Priority.choices,
    }
    return render(request, 'technician/tickets.html', context)

@login_required
@user_passes_test(is_technician)
def technician_ticket_detail(request, ticket_id):
    ticket = get_object_or_404(Ticket.objects.select_related(
        'service', 'created_by', 'assigned_to'
    ), id=ticket_id)
    
    comments = Comment.objects.filter(ticket=ticket).order_by('created_at')
    attachments = TicketAttachment.objects.filter(ticket=ticket)
    
    context = {
        'ticket': ticket,
        'comments': comments,
        'attachments': attachments,
        'status_choices': Ticket.Status.choices,
        'priority_choices': Ticket.Priority.choices,
    }
    return render(request, 'technician/ticket_detail.html', context)

@login_required
@user_passes_test(is_technician)
def technician_create_ticket(request):
    if request.method == 'POST':
        service_id = request.POST.get('service')
        title = request.POST.get('title')
        description = request.POST.get('description')
        priority = request.POST.get('priority', 'normal')
        
        if not all([service_id, title, description]):
            messages.error(request, 'Please fill in all required fields.')
            return redirect('core:technician_create_ticket')
        
        ticket = Ticket.objects.create(
            service_id=service_id,
            title=title,
            description=description,
            priority=priority,
            created_by=request.user,
            assigned_to=request.user,
            status='in_progress'
        )
        
        messages.success(request, 'Ticket created successfully.')
        return redirect('core:technician_ticket_detail', ticket_id=ticket.id)
    
    services = Service.objects.filter(is_active=True)
    context = {
        'services': services,
        'priority_choices': Ticket.Priority.choices,
    }
    return render(request, 'technician/create_ticket.html', context)

@login_required
def technician_update_ticket(request, ticket_id):
    if not is_technician(request.user):
        messages.error(request, "Access denied. You must be a technician to update tickets.")
        return redirect('core:dashboard')

    ticket = get_object_or_404(Ticket, id=ticket_id)
    
    if request.method == 'POST':
        # Get form data
        status = request.POST.get('status')
        priority = request.POST.get('priority')
        note = request.POST.get('note')
        notify_user = request.POST.get('notify_user', 'off') == 'on'
        
        # Create comment if note provided
        if note:
            Comment.objects.create(
                ticket=ticket,
                author=request.user,
                content=note,
                is_internal=not notify_user
            )
        
        # Update ticket fields
        if status:
            old_status = ticket.status
            ticket.status = status
            if status == 'resolved':
                ticket.resolved_at = timezone.now()
            # Log status change
            logger.info(f"Ticket #{ticket.id} status changed from {old_status} to {status}")
        
        if priority:
            ticket.priority = priority
        
        ticket.updated_at = timezone.now()
        ticket.save()
        
        if notify_user and status != ticket.status:
            try:
                # Send email notification to user
                subject = f'Ticket #{ticket.id} Status Update'
                message = f'''
                Your ticket has been updated:
                
                Status: {ticket.get_status_display()}
                
                {note if note else ''}
                
                View ticket: http://{request.get_host()}/tickets/{ticket.id}/
                '''
                send_mail(
                    subject,
                    message,
                    settings.DEFAULT_FROM_EMAIL,
                    [ticket.created_by.email],
                    fail_silently=True,
                )
            except Exception as e:
                logger.error(f"Failed to send notification email: {str(e)}")
        
        messages.success(request, 'Ticket updated successfully.')
    
    return redirect('core:technician_ticket_detail', ticket_id=ticket_id)

@login_required
def technician_resolve_ticket(request, ticket_id):
    if not is_technician(request.user):
        messages.error(request, "Access denied. You must be a technician to resolve tickets.")
        return redirect('core:dashboard')

    ticket = get_object_or_404(Ticket, id=ticket_id)
    
    if request.method == 'POST':
        resolution = request.POST.get('resolution')
        notify_user = request.POST.get('notify_user', 'off') == 'on'
        
        if not resolution:
            messages.error(request, 'Please provide a resolution summary.')
            return redirect('core:technician_ticket_detail', ticket_id=ticket_id)
        
        # Update ticket status
        ticket.status = 'resolved'
        ticket.resolution = resolution
        ticket.resolved_at = timezone.now()
        ticket.save()
        
        # Create resolution comment
        comment = Comment.objects.create(
            ticket=ticket,
            author=request.user,
            content=f"Ticket resolved: {resolution}",
            is_internal=False  # Resolution comments should be visible to users
        )
        
        # Handle notification
        if notify_user:
            try:
                subject = f'Ticket #{ticket.id} Resolved'
                message = f'''
                Your ticket has been resolved:

                Resolution: {resolution}

                View ticket: http://{request.get_host()}/tickets/{ticket.id}/
                '''
                send_mail(
                    subject,
                    message,
                    settings.DEFAULT_FROM_EMAIL,
                    [ticket.created_by.email],
                    fail_silently=True,
                )
            except Exception as e:
                logger.error(f"Failed to send resolution notification: {str(e)}")
        
        messages.success(request, 'Ticket resolved successfully.')
    
    return redirect('core:technician_ticket_detail', ticket_id=ticket_id)

@login_required
@user_passes_test(is_technician)
def technician_close_ticket(request, ticket_id):
    ticket = get_object_or_404(Ticket, id=ticket_id)
    
    if request.method == 'POST':
        note = request.POST.get('note', '')
        if ticket.status != 'resolved':
            messages.error(request, 'Only resolved tickets can be closed.')
            return redirect('core:technician_ticket_detail', ticket_id=ticket_id)
        
        ticket.status = 'closed'
        ticket.save()

        # Add closure note if provided
        if note:
            Comment.objects.create(
                ticket=ticket,
                author=request.user,
                content=f"Ticket closed: {note}",
                is_internal=False
            )
        
        messages.success(request, 'Ticket closed successfully.')
    
    return redirect('core:technician_ticket_detail', ticket_id=ticket_id)

@login_required
def technician_transfer_ticket(request, ticket_id):
    if not is_technician(request.user):
        messages.error(request, "Access denied. You must be a technician to transfer tickets.")
        return redirect('core:dashboard')

    ticket = get_object_or_404(Ticket, id=ticket_id)
    
    if request.method == 'POST':
        technician_id = request.POST.get('technician')
        transfer_note = request.POST.get('note', '')
        notify_technician = request.POST.get('notify_technician', 'off') == 'on'
        
        if not technician_id:
            messages.error(request, 'Please select a technician.')
            return redirect('core:technician_ticket_detail', ticket_id=ticket_id)
        
        try:
            new_technician = User.objects.get(id=technician_id, role='technician')
            old_technician = ticket.assigned_to
            
            # Update ticket assignment
            ticket.assigned_to = new_technician
            ticket.save()
            
            # Create transfer note
            note_content = f"Ticket transferred from {old_technician.get_full_name() if old_technician else 'unassigned'} to {new_technician.get_full_name()}"
            if transfer_note:
                note_content += f"\nTransfer note: {transfer_note}"
                
            Comment.objects.create(
                ticket=ticket,
                author=request.user,
                content=note_content,
                is_internal=True  # Transfer notes are internal
            )
            
            # Send notification to new technician
            if notify_technician:
                try:
                    subject = f'Ticket #{ticket.id} Assigned to You'
                    message = f'''
                    A ticket has been transferred to you:

                    Ticket: #{ticket.id} - {ticket.title}
                    From: {old_technician.get_full_name() if old_technician else 'Unassigned'}
                    Status: {ticket.get_status_display()}
                    Priority: {ticket.get_priority_display()}
                    
                    {f"Note: {transfer_note}" if transfer_note else ""}

                    View ticket: http://{request.get_host()}/technician/tickets/{ticket.id}/
                    '''
                    send_mail(
                        subject,
                        message,
                        settings.DEFAULT_FROM_EMAIL,
                        [new_technician.email],
                        fail_silently=True,
                    )
                except Exception as e:
                    logger.error(f"Failed to send transfer notification: {str(e)}")
            
            messages.success(request, f'Ticket transferred to {new_technician.get_full_name()}.')
            logger.info(f"Ticket #{ticket.id} transferred to {new_technician.email}")
            
        except User.DoesNotExist:
            messages.error(request, 'Selected technician not found.')
            logger.error(f"Transfer failed - Technician not found: {technician_id}")
    
    return redirect('core:technician_ticket_detail', ticket_id=ticket_id)

@login_required
def technician_print_ticket(request, ticket_id):
    if not is_technician(request.user):
        messages.error(request, "Access denied. You must be a technician to print tickets.")
        return redirect('core:dashboard')
    
    ticket = get_object_or_404(Ticket.objects.select_related(
        'service', 'created_by', 'assigned_to'
    ), id=ticket_id)
    
    comments = Comment.objects.filter(ticket=ticket).order_by('created_at')
    attachments = TicketAttachment.objects.filter(ticket=ticket)
    
    context = {
        'ticket': ticket,
        'comments': comments,
        'attachments': attachments,
        'now': timezone.now(),
    }
    return render(request, 'technician/ticket_print.html', context)

@login_required
@user_passes_test(is_technician)
def technician_assign_ticket(request, ticket_id):
    ticket = get_object_or_404(Ticket, id=ticket_id)
    
    if request.method == 'POST':
        ticket.assigned_to = request.user
        ticket.status = 'in_progress'
        ticket.save()
        messages.success(request, 'Ticket assigned to you successfully.')
    
    return redirect('core:technician_ticket_detail', ticket_id=ticket_id)

@login_required
def technician_escalate_ticket(request, ticket_id):
    if not is_technician(request.user):
        messages.error(request, "Access denied. You must be a technician to escalate tickets.")
        return redirect('core:dashboard')

    ticket = get_object_or_404(Ticket, id=ticket_id)
    
    if request.method == 'POST':
        reason = request.POST.get('reason')
        escalation_level = request.POST.get('level', 'level_2')
        note = request.POST.get('note', '')
        notify_managers = request.POST.get('notify_managers', 'off') == 'on'
        
        if not reason:
            messages.error(request, 'Please provide an escalation reason.')
            return redirect('core:technician_ticket_detail', ticket_id=ticket_id)
        
        # Update ticket
        old_priority = ticket.priority
        ticket.priority = 'urgent'
        ticket.escalation_level = escalation_level
        ticket.save()
        
        # Create escalation note
        note_content = f"Ticket escalated\nReason: {reason}\nLevel: {escalation_level}"
        if note:
            note_content += f"\nAdditional notes: {note}"
            
        Comment.objects.create(
            ticket=ticket,
            author=request.user,
            content=note_content,
            is_internal=True  # Escalation notes are internal
        )
        
        # Notify managers if requested
        if notify_managers:
            try:
                managers = User.objects.filter(is_staff=True, is_active=True)
                if managers.exists():
                    subject = f'Urgent: Ticket #{ticket.id} Escalated'
                    message = f'''
                    A ticket has been escalated:

                    Ticket: #{ticket.id} - {ticket.title}
                    Priority: {old_priority} → Urgent
                    Escalation Level: {escalation_level}
                    Reason: {reason}
                    
                    {f"Additional Notes: {note}" if note else ""}

                    View ticket: http://{request.get_host()}/technician/tickets/{ticket.id}/
                    '''
                    
                    send_mail(
                        subject,
                        message,
                        settings.DEFAULT_FROM_EMAIL,
                        [manager.email for manager in managers],
                        fail_silently=True,
                    )
            except Exception as e:
                logger.error(f"Failed to send escalation notification: {str(e)}")
        
        logger.info(f"Ticket #{ticket.id} escalated to {escalation_level} by {request.user.email}")
        messages.success(request, 'Ticket escalated successfully.')
    
    return redirect('core:technician_ticket_detail', ticket_id=ticket_id)

@login_required
def technician_add_comment(request, ticket_id):
    if not is_technician(request.user):
        messages.error(request, "Access denied. You must be a technician to add comments.")
        return redirect('core:dashboard')

    ticket = get_object_or_404(Ticket, id=ticket_id)
    
    if request.method == 'POST':
        content = request.POST.get('content')
        is_internal = request.POST.get('is_internal') == 'on'
        
        if not content:
            messages.error(request, 'Please enter a comment.')
            return redirect('core:technician_ticket_detail', ticket_id=ticket_id)
        
        # Create the comment
        comment = Comment.objects.create(
            ticket=ticket,
            author=request.user,
            content=content,
            is_internal=is_internal
        )
        
        # Handle attachments
        if request.FILES.getlist('attachments'):
            for file in request.FILES.getlist('attachments'):
                if file.size > 5 * 1024 * 1024:  # 5MB limit
                    messages.warning(request, f'File {file.name} exceeds 5MB size limit')
                    continue
                
                TicketAttachment.objects.create(
                    ticket=ticket,
                    file=file,
                    uploaded_by=request.user,
                    comment=comment
                )
        
        # Update ticket status if it's new
        if ticket.status == 'new':
            ticket.status = 'in_progress'
            ticket.save()
            messages.info(request, 'Ticket status updated to In Progress.')
        
        messages.success(request, 'Comment added successfully.')
    
    return redirect('core:technician_ticket_detail', ticket_id=ticket_id)

@login_required
@user_passes_test(is_technician)
def technician_profile(request):
    """
    Display the technician's profile page with statistics, skills, and activity.
    """
    # Get technician profile (create if doesn't exist)
    technician_profile, created = TechnicianProfile.objects.get_or_create(user=request.user)
    
    # Get ticket statistics
    assigned_tickets = Ticket.objects.filter(assigned_to=request.user)
    assigned_tickets_count = assigned_tickets.count()
    
    resolved_tickets = assigned_tickets.filter(status='resolved')
    resolved_tickets_count = resolved_tickets.count()
    
    open_tickets = assigned_tickets.filter(status='open')
    open_tickets_count = open_tickets.count()
    
    # Calculate average resolution time
    avg_resolution_time = 0
    if resolved_tickets.exists():
        resolution_times = []
        for ticket in resolved_tickets:
            if ticket.resolved_at and ticket.created_at:
                resolution_time = (ticket.resolved_at - ticket.created_at).total_seconds() / 3600  # hours
                resolution_times.append(resolution_time)
        
        if resolution_times:
            avg_resolution_time = sum(resolution_times) / len(resolution_times)
    
        # Calculate efficiency based on a 24-hour target
        efficiency = 0
        if avg_resolution_time >= 0: # Ensure avg_resolution_time is not negative
            # Efficiency decreases as resolution time increases
            # Target time is 24 hours. Efficiency is 100% at 0 hours, 0% at 24 hours.
            # Formula: (TargetTime - ActualTime) / TargetTime * 100
            target_time = 24
            efficiency = max(0, (target_time - avg_resolution_time) / target_time * 100) # Ensure efficiency is not negative
    
    # Get KB articles count
    kb_articles_count = KnowledgeBaseArticle.objects.filter(created_by=request.user).count()
    
    # Get recent activity
    recent_tickets = assigned_tickets.order_by('-updated_at')[:5]
    
    # Get recent comments by the technician
    recent_comments = Comment.objects.filter(
        author=request.user
    ).order_by('-created_at')[:5]
    
    # Calculate performance metrics
    resolution_rate = 0
    if assigned_tickets_count > 0:
        resolution_rate = (resolved_tickets_count / assigned_tickets_count) * 100
    
    # Get customer satisfaction rating (if available)
    satisfaction_rating = 4.5  # Default value, should be calculated from actual feedback
    
    # Performance metrics
    performance = {
        'resolution_rate': resolution_rate,
        'avg_resolution_time': round(avg_resolution_time, 1),
        'customer_satisfaction': satisfaction_rating,
        'efficiency': round(efficiency, 1) # Add efficiency here
    }
    
    # Check if technician is available
    is_available = technician_profile.is_available
    
    context = {
        'technician_profile': technician_profile,
        'assigned_tickets_count': assigned_tickets_count,
        'resolved_tickets_count': resolved_tickets_count,
        'open_tickets_count': open_tickets_count,
        'kb_articles_count': kb_articles_count,
        'recent_tickets': recent_tickets,
        'recent_comments': recent_comments,
        'performance': performance,
        'is_available': is_available,
    }
    
    return render(request, 'technician/profile.html', context)

def technician_knowledge_base(request):
    """
    Display the knowledge base articles for technicians with filtering and search capabilities.
    """
    # Get filter parameters
    category_id = request.GET.get('category')
    tag = request.GET.get('tag')
    search = request.GET.get('search')
    sort_by = request.GET.get('sort', 'latest')
    
    # Assuming we have a KnowledgeBaseArticle model
    try:
        from apps.kb.models import KnowledgeBaseArticle, ArticleCategory, Tag
        
        # Base queryset
        articles_query = KnowledgeBaseArticle.objects.all()
        
        # Apply filters
        if category_id:
            articles_query = articles_query.filter(category_id=category_id)
        
        if tag:
            articles_query = articles_query.filter(tags_json__icontains=tag)
            
        if search:
            articles_query = articles_query.filter(
                models.Q(title__icontains=search) | 
                models.Q(content__icontains=search) |
                models.Q(short_description__icontains=search)
            )
        
        # Apply sorting
        if sort_by == 'latest':
            articles_query = articles_query.order_by('-updated_at')
        elif sort_by == 'oldest':
            articles_query = articles_query.order_by('created_at')
        elif sort_by == 'views':
            articles_query = articles_query.order_by('-views')
        elif sort_by == 'a-z':
            articles_query = articles_query.order_by('title')
        
        # Get all categories
        categories = ArticleCategory.objects.all()
        
        # Get popular tags - Fix the query to not use a reverse relationship
        # We'll count the occurrences in tags_json field
        from django.db.models import Count
        import json
        
        # First get all tags
        all_tags = Tag.objects.all()
        
        # Create a dictionary to count how many articles use each tag
        tag_counts = {}
        for tag in all_tags:
            tag_counts[tag.name] = KnowledgeBaseArticle.objects.filter(tags_json__icontains=tag.name).count()
        
        # Sort tags by count and get top 10
        sorted_tags = sorted(all_tags, key=lambda t: tag_counts.get(t.name, 0), reverse=True)
        popular_tags = sorted_tags[:10]
        
        # Get featured articles
        featured_articles = KnowledgeBaseArticle.objects.filter(
            is_featured=True
        ).order_by('-updated_at')[:4]
        
        # Paginate results
        paginator = Paginator(articles_query, 12)  # Show 12 articles per page
        page_number = request.GET.get('page', 1)
        articles = paginator.get_page(page_number)
        
        context = {
            'articles': articles,
            'featured_articles': featured_articles,
            'categories': categories,
            'popular_tags': popular_tags,
            'category': category_id,
            'tag': tag,
            'search': search,
            'sort_by': sort_by,
            'is_admin': request.user.is_staff,
        }
        
    except ImportError:
        # If KB app isn't configured yet, show empty state
        context = {
            'articles': [],
            'featured_articles': [],
            'categories': [],
            'popular_tags': [],
            'is_admin': request.user.is_staff,
        }
    
    return render(request, 'technician/knowledge_base.html', context)

def technician_article_detail(request, article_id):
    """
    Display the details of a knowledge base article.
    """
    try:
        from apps.kb.models import KnowledgeBaseArticle
        
        # Get the article
        article = get_object_or_404(KnowledgeBaseArticle, id=article_id)
        
        # Increment view count if not viewed by the author
        if request.user != article.created_by:
            article.views = models.F('views') + 1
            article.save(update_fields=['views'])
            article.refresh_from_db()
        
        # Get related articles
        related_articles = article.related_articles.all()[:3]
        
        # Get similar articles based on tags
        similar_articles = []
        if article.tags:
            # Parse tags JSON if stored as a JSON string
            tags = article.tags
            if isinstance(tags, str):
                try:
                    tags = json.loads(tags)
                except:
                    tags = []
            
            # Get articles with similar tags
            similar_query = KnowledgeBaseArticle.objects.exclude(id=article_id)
            for tag in tags:
                similar_query = similar_query.filter(tags__icontains=tag)
            
            similar_articles = similar_query.order_by('-views')[:3]
        
        context = {
            'article': article,
            'related_articles': related_articles,
            'similar_articles': similar_articles,
            'can_edit': request.user.is_staff or request.user == article.created_by,
        }
        
    except ImportError:
        # Fallback if KB app isn't configured
        context = {
            'article': {'id': article_id, 'title': 'Article not found'},
            'error': 'Knowledge base module is not installed',
        }
    
    return render(request, 'technician/article_detail.html', context)

def technician_create_article(request):
    """
    Handle knowledge base article creation.
    """
    if not request.user.is_staff and request.user.role != 'technician':
        messages.error(request, 'You do not have permission to create knowledge base articles.')
        return redirect('core:technician_knowledge_base')
    
    try:
        from apps.kb.models import KnowledgeBaseArticle, ArticleCategory
        
        if request.method == 'POST':
            # Get form data
            title = request.POST.get('title')
            category_id = request.POST.get('category')
            new_category = request.POST.get('new_category')
            short_description = request.POST.get('short_description')
            content = request.POST.get('content')
            tags = request.POST.get('tags', '[]')
            is_featured = bool(request.POST.get('is_featured'))
            status = request.POST.get('status', 'published')
            visibility = request.POST.get('visibility', 'public')
            related_articles_ids = request.POST.getlist('related_articles')
            
            # Validate required fields
            if not all([title, short_description, content, visibility]) or (not category_id and not new_category):
                messages.error(request, 'Please fill in all required fields.')
                return redirect('core:technician_create_article')
            
            # Create or get category
            if category_id == 'new' and new_category:
                category, created = ArticleCategory.objects.get_or_create(
                    name=new_category,
                    defaults={'created_by': request.user}
                )
                category_id = category.id
            
            # Create the article
            article = KnowledgeBaseArticle.objects.create(
                title=title,
                category_id=category_id,
                short_description=short_description,
                content=content,
                is_featured=is_featured,
                status=status,
                visibility=visibility,
                created_by=request.user,
                updated_by=request.user
            )

            # Handle tags
            try:
                article.tags = tags
                article.save()
            except Exception as e:
                logger.error(f"Error setting tags for article {article.id}: {str(e)}")
            
            # Add related articles
            if related_articles_ids:
                related_articles = KnowledgeBaseArticle.objects.filter(id__in=related_articles_ids)
                article.related_articles.add(*related_articles)
            
            # Handle file attachments
            if 'attachments' in request.FILES:
                files = request.FILES.getlist('attachments')
                for file in files:
                    if file.size > 10 * 1024 * 1024:  # 10MB limit
                        messages.warning(request, f'File {file.name} exceeds the 10MB size limit and was not uploaded.')
                        continue
                    article.attachments.create(file=file)
            
            messages.success(request, 'Article created successfully.')
            return redirect('core:technician_article_detail', article_id=article.id)
        
        # Get data for the form
        categories = ArticleCategory.objects.all()
        all_articles = KnowledgeBaseArticle.objects.exclude(status='draft').order_by('-created_at')
        
        context = {
            'categories': categories,
            'all_articles': all_articles,
        }
        
    except ImportError:
        # Fallback if KB app isn't configured
        messages.error(request, 'Knowledge base module is not installed.')
        return redirect('core:technician_dashboard')
    
    return render(request, 'technician/create_article.html', context)

def technician_edit_article(request, article_id):
    """
    Handle knowledge base article editing.
    """
    try:
        from apps.kb.models import KnowledgeBaseArticle, ArticleCategory
        
        # Get the article
        article = get_object_or_404(KnowledgeBaseArticle, id=article_id)
        
        # Check permissions
        if not request.user.is_staff and request.user != article.created_by:
            messages.error(request, 'You do not have permission to edit this article.')
            return redirect('core:technician_article_detail', article_id=article_id)
        
        if request.method == 'POST':
            # Get form data
            title = request.POST.get('title')
            category_id = request.POST.get('category')
            new_category = request.POST.get('new_category')
            short_description = request.POST.get('short_description')
            content = request.POST.get('content')
            tags_json = request.POST.get('tags', '[]')
            is_featured = bool(request.POST.get('is_featured'))
            status = request.POST.get('status', 'published')
            visibility = request.POST.get('visibility', 'public')
            related_articles_ids = request.POST.getlist('related_articles')
            create_revision = bool(request.POST.get('create_revision'))
            delete_attachments = request.POST.getlist('delete_attachments')
            
            # Validate required fields
            if not all([title, short_description, content, visibility]) or (not category_id and not new_category):
                messages.error(request, 'Please fill in all required fields.')
                return redirect('core:technician_edit_article', article_id=article_id)
            
            # Create or get category
            if category_id == 'new' and new_category:
                category, created = ArticleCategory.objects.get_or_create(
                    name=new_category,
                    defaults={'created_by': request.user}
                )
                category_id = category.id
            
            # Create revision if requested
            if create_revision:
                from apps.kb.models import ArticleRevision
                ArticleRevision.objects.create(
                    article=article,
                    title=article.title,
                    content=article.content,
                    short_description=article.short_description,
                    tags_json=article.tags_json,
                    status=article.status,
                    created_by=request.user
                )
            
            # Update the article
            article.title = title
            article.category_id = category_id
            article.short_description = short_description
            article.content = content
            article.tags_json = tags_json
            article.is_featured = is_featured
            article.status = status
            article.visibility = visibility
            article.updated_by = request.user
            article.save()
            
            # Update related articles
            article.related_articles.clear()
            if related_articles_ids:
                related_articles = KnowledgeBaseArticle.objects.filter(id__in=related_articles_ids)
                article.related_articles.add(*related_articles)
            
            # Delete attachments
            if delete_attachments:
                article.attachments.filter(id__in=delete_attachments).delete()
            
            # Handle file attachments
            if 'attachments' in request.FILES:
                files = request.FILES.getlist('attachments')
                for file in files:
                    if file.size > 10 * 1024 * 1024:  # 10MB limit
                        messages.warning(request, f'File {file.name} exceeds the 10MB size limit and was not uploaded.')
                        continue
                    article.attachments.create(file=file)
            
            messages.success(request, 'Article updated successfully.')
            return redirect('core:technician_article_detail', article_id=article.id)
        
        # Get data for the form
        categories = ArticleCategory.objects.all()
        all_articles = KnowledgeBaseArticle.objects.exclude(id=article_id).exclude(status='draft').order_by('-created_at')
        
        context = {
            'article': article,
            'categories': categories,
            'all_articles': all_articles,
        }
        
    except ImportError:
        # Fallback if KB app isn't configured
        messages.error(request, 'Knowledge base module is not installed.')
        return redirect('core:technician_dashboard')
    
    return render(request, 'technician/edit_article.html', context)

def technician_delete_article(request, article_id):
    """
    Handle knowledge base article deletion.
    """
    if request.method != 'POST':
        return redirect('core:technician_article_detail', article_id=article_id)
    
    try:
        from apps.kb.models import KnowledgeBaseArticle
        
        # Get the article
        article = get_object_or_404(KnowledgeBaseArticle, id=article_id)
        
        # Check permissions
        if not request.user.is_staff and request.user != article.created_by:
            messages.error(request, 'You do not have permission to delete this article.')
            return redirect('core:technician_article_detail', article_id=article_id)
        
        # Delete the article
        title = article.title  # Save for message
        article.delete()
        
        messages.success(request, f'Article "{title}" deleted successfully.')
        return redirect('core:technician_knowledge_base')
        
    except ImportError:
        # Fallback if KB app isn't configured
        messages.error(request, 'Knowledge base module is not installed.')
        return redirect('core:technician_dashboard')

@login_required
@require_POST
def technician_article_feedback(request, article_id):
    """
    Handle article feedback submission.
    """
    try:
        from apps.kb.models import KnowledgeBaseArticle, ArticleFeedback
        
        # Get the article
        article = get_object_or_404(KnowledgeBaseArticle, id=article_id)
        
        # Parse JSON data
        try:
            data = json.loads(request.body)
            is_helpful = data.get('is_helpful', False)
            comment = data.get('comment', '')
        except json.JSONDecodeError:
            return JsonResponse({'status': 'error', 'message': 'Invalid JSON'}, status=400)
        
        # Save feedback
        feedback = ArticleFeedback.objects.create(
            article=article,
            user=request.user,
            is_helpful=is_helpful,
            comment=comment,
            ip_address=request.META.get('REMOTE_ADDR')
        )
        
        return JsonResponse({'status': 'success', 'message': 'Feedback submitted successfully'})
        
    except ImportError:
        # Fallback if KB app isn't configured
        return JsonResponse({'status': 'error', 'message': 'Knowledge base module is not installed'}, status=500)

from django import forms
from django.utils.translation import gettext_lazy as _
from django.contrib.auth.forms import UserCreationForm, PasswordChangeForm
from apps.accounts.models import User
from .models import Profile, FAQ
from apps.tickets.models import Ticket

class ContactForm(forms.Form):
    """Contact form for the contact page"""
    name = forms.CharField(max_length=100)
    email = forms.EmailField()
    subject = forms.CharField(max_length=200)
    message = forms.CharField(widget=forms.Textarea)

class RegistrationForm(UserCreationForm):
    """Form for user registration"""
    email = forms.EmailField(required=True)
    first_name = forms.CharField(max_length=30, required=True)
    last_name = forms.CharField(max_length=30, required=True)
    
    class Meta:
        model = User
        fields = ('email', 'first_name', 'last_name', 'password1', 'password2')
    
    def clean_email(self):
        email = self.cleaned_data['email']
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError(_("A user with this email already exists."))
        return email
    
    def save(self, commit=True):
        user = super().save(commit=False)
        user.username = user.email  # Use email as username
        user.role = 'customer'  # Default role is customer
        if commit:
            user.save()
        return user

class ProfileForm(forms.ModelForm):
    """Form for updating user profile"""
    first_name = forms.CharField(max_length=30, required=True)
    last_name = forms.CharField(max_length=30, required=True)
    
    class Meta:
        model = Profile
        fields = ('company', 'phone', 'preferred_contact_method')
    
    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        if self.user:
            self.fields['first_name'].initial = self.user.first_name
            self.fields['last_name'].initial = self.user.last_name
    
    def save(self, commit=True):
        profile = super().save(commit=False)
        if self.user:
            self.user.first_name = self.cleaned_data['first_name']
            self.user.last_name = self.cleaned_data['last_name']
            if commit:
                self.user.save()
        if commit:
            profile.save()
        return profile

class CustomPasswordChangeForm(PasswordChangeForm):
    """Custom form for changing password"""
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['old_password'].widget.attrs.update({'class': 'form-control'})
        self.fields['new_password1'].widget.attrs.update({'class': 'form-control'})
        self.fields['new_password2'].widget.attrs.update({'class': 'form-control'})

class ServiceRequestForm(forms.Form):
    """Form for requesting a service"""
    service_id = forms.IntegerField(widget=forms.HiddenInput())
    first_name = forms.CharField(max_length=100)
    last_name = forms.CharField(max_length=100)
    email = forms.EmailField()
    phone = forms.CharField(max_length=20, required=False)
    company = forms.CharField(max_length=255, required=False)
    message = forms.CharField(widget=forms.Textarea)
    preferred_contact = forms.ChoiceField(
        choices=[('email', 'Email'), ('phone', 'Phone'), ('both', 'Both')],
        initial='email'
    )

class TicketForm(forms.ModelForm):
    """Form for creating tickets"""
    # Removed the attachments field - we'll handle file uploads manually in the view
    
    class Meta:
        model = Ticket
        fields = ['title', 'description', 'priority', 'category', 'device_type', 'device_model']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 5}),
        }

class FAQFeedbackForm(forms.Form):
    """Form for collecting feedback on FAQs"""
    faq_id = forms.IntegerField(widget=forms.HiddenInput())
    helpful = forms.BooleanField(required=False)
    comment = forms.CharField(widget=forms.Textarea(attrs={'rows': 2}), required=False) 
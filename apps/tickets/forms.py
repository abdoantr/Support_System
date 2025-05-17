from django import forms
from django.utils.translation import gettext_lazy as _
from .models import Ticket, TicketComment, TicketAttachment
from apps.accounts.models import User

class TicketForm(forms.ModelForm):
    """Form for creating and updating tickets"""
    
    attachments = forms.FileField(
        widget=forms.ClearableFileInput(attrs={'multiple': True}),
        required=False
    )
    
    class Meta:
        model = Ticket
        fields = ['title', 'description', 'priority', 'category', 'device_type', 'device_model']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 5}),
        }
    
    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)

class TicketAdminForm(forms.ModelForm):
    """Admin form for updating tickets"""
    
    class Meta:
        model = Ticket
        fields = ['title', 'description', 'status', 'priority', 'assigned_to', 
                 'due_date', 'category', 'device_type', 'device_model']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 5}),
            'due_date': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Filter the assigned_to field to only show technicians
        self.fields['assigned_to'].queryset = User.objects.filter(role='technician', is_active=True)

class TicketCommentForm(forms.ModelForm):
    """Form for creating and updating ticket comments"""
    
    class Meta:
        model = TicketComment
        fields = ['content', 'is_internal']
        widgets = {
            'content': forms.Textarea(attrs={'rows': 3}),
        }
    
    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        self.ticket = kwargs.pop('ticket', None)
        super().__init__(*args, **kwargs)
        
        # Only staff and technicians can create internal comments
        if self.user and not (self.user.is_staff or self.user.role == 'technician'):
            self.fields.pop('is_internal')
    
    def save(self, commit=True):
        instance = super().save(commit=False)
        if self.user:
            instance.author = self.user
        if self.ticket:
            instance.ticket = self.ticket
        if commit:
            instance.save()
        return instance

class TicketAttachmentForm(forms.ModelForm):
    """Form for creating and updating ticket attachments"""
    
    class Meta:
        model = TicketAttachment
        fields = ['file', 'description']
    
    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        self.ticket = kwargs.pop('ticket', None)
        super().__init__(*args, **kwargs)
    
    def save(self, commit=True):
        instance = super().save(commit=False)
        if self.user:
            instance.uploaded_by = self.user
        if self.ticket:
            instance.ticket = self.ticket
        if commit:
            instance.save()
        return instance

class TicketStatusForm(forms.Form):
    """Form for changing ticket status"""
    
    status = forms.ChoiceField(choices=Ticket.Status.choices)

class TicketAssignForm(forms.Form):
    """Form for assigning tickets to technicians"""
    
    technician = forms.ModelChoiceField(
        queryset=User.objects.filter(role='technician', is_active=True)
    ) 
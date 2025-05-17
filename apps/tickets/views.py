from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.utils import timezone
from django.db.models import Q
from drf_spectacular.utils import extend_schema, OpenApiParameter
from .models import Ticket, TicketComment, TicketAttachment
from .serializers import (
    TicketSerializer, TicketCreateSerializer,
    TicketCommentSerializer, TicketAttachmentSerializer
)
from apps.accounts.permissions import IsTechnician
from apps.accounts.models import User

class IsTicketOwnerOrStaff(permissions.BasePermission):
    """
    Custom permission to only allow owners of a ticket or staff to view or edit it.
    """
    def has_object_permission(self, request, view, obj):
        # Staff can do anything
        if request.user.is_staff or request.user.role == 'technician':
            return True
            
        # Otherwise, only ticket creator can access it
        return obj.created_by == request.user

class TicketViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows tickets to be viewed or edited.
    
    Regular users can only see tickets they created.
    Technicians can see tickets assigned to them or unassigned tickets.
    Admins can see all tickets.
    """
    serializer_class = TicketSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if user.role == 'admin':
            return Ticket.objects.all()
        elif user.role == 'technician':
            return Ticket.objects.filter(
                Q(assigned_to=user) | Q(assigned_to=None)
            )
        return Ticket.objects.filter(created_by=user)

    def get_serializer_class(self):
        if self.action == 'create':
            return TicketCreateSerializer
        return TicketSerializer

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)

    @extend_schema(
        description="Assign a ticket to a technician",
        request={'application/json': {'properties': {'technician_id': {'type': 'integer'}}}},
        responses={200: TicketSerializer}
    )
    @action(detail=True, methods=['post'], permission_classes=[permissions.IsAdminUser | IsTechnician])
    def assign(self, request, pk=None):
        ticket = self.get_object()
        technician_id = request.data.get('technician_id')
        
        if not technician_id:
            return Response(
                {'error': 'Technician ID is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            technician = User.objects.get(id=technician_id, role='technician')
            ticket.assigned_to = technician
            ticket.status = Ticket.Status.ASSIGNED
            ticket.save(update_fields=['assigned_to', 'status'])
            return Response(TicketSerializer(ticket).data)
        except User.DoesNotExist:
            return Response(
                {'error': 'Technician not found'},
                status=status.HTTP_404_NOT_FOUND
            )

    @extend_schema(
        description="Change the status of a ticket",
        request={'application/json': {'properties': {'status': {'type': 'string'}}}},
        responses={200: TicketSerializer}
    )
    @action(detail=True, methods=['post'], permission_classes=[permissions.IsAuthenticated, IsTicketOwnerOrStaff])
    def change_status(self, request, pk=None):
        ticket = self.get_object()
        new_status = request.data.get('status')
        
        if new_status not in dict(Ticket.Status.choices):
            return Response(
                {'error': 'Invalid status'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        ticket.status = new_status
        if new_status == Ticket.Status.RESOLVED:
            ticket.resolved_at = timezone.now()
        ticket.save(update_fields=['status', 'resolved_at'] if new_status == Ticket.Status.RESOLVED else ['status'])
        return Response(TicketSerializer(ticket).data)
        
    @extend_schema(
        description="Get tickets with a specific status",
        parameters=[
            OpenApiParameter(name="status", description="Ticket status", required=True, type=str)
        ],
        responses={200: TicketSerializer(many=True)}
    )
    @action(detail=False, methods=['get'])
    def by_status(self, request):
        status_param = request.query_params.get('status')
        if not status_param or status_param not in dict(Ticket.Status.choices):
            return Response(
                {'error': 'Valid status parameter is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
            
        tickets = self.get_queryset().filter(status=status_param)
        page = self.paginate_queryset(tickets)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
            
        serializer = self.get_serializer(tickets, many=True)
        return Response(serializer.data)

class TicketCommentViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows ticket comments to be viewed or edited.
    
    Regular users can only see comments for tickets they created, and cannot see internal comments.
    Technicians can see comments for tickets assigned to them.
    Admins can see all comments.
    """
    serializer_class = TicketCommentSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if user.role == 'admin':
            return TicketComment.objects.all()
        elif user.role == 'technician':
            return TicketComment.objects.filter(
                ticket__assigned_to=user
            )
        return TicketComment.objects.filter(
            ticket__created_by=user,
            is_internal=False
        )

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)

class TicketAttachmentViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows ticket attachments to be viewed or edited.
    """
    serializer_class = TicketAttachmentSerializer
    permission_classes = [permissions.IsAuthenticated, IsTicketOwnerOrStaff]

    def get_queryset(self):
        ticket_pk = self.kwargs.get('ticket_pk')
        return TicketAttachment.objects.filter(ticket_id=ticket_pk)

    def perform_create(self, serializer):
        serializer.save(
            uploaded_by=self.request.user,
            ticket_id=self.kwargs.get('ticket_pk')
        )
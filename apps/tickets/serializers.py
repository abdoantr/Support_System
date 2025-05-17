from rest_framework import serializers
from .models import Ticket, TicketComment, TicketAttachment
from apps.accounts.serializers import UserSerializer

class TicketAttachmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = TicketAttachment
        fields = '__all__'
        read_only_fields = ('uploaded_by',)

class TicketCommentSerializer(serializers.ModelSerializer):
    author_details = UserSerializer(source='author', read_only=True)

    class Meta:
        model = TicketComment
        fields = ('id', 'ticket', 'author', 'author_details', 
                 'content', 'created_at', 'is_internal')
        read_only_fields = ('author',)

class TicketSerializer(serializers.ModelSerializer):
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    priority_display = serializers.CharField(source='get_priority_display', read_only=True)
    created_by_details = UserSerializer(source='created_by', read_only=True)
    assigned_to_details = UserSerializer(source='assigned_to', read_only=True)
    comments = TicketCommentSerializer(many=True, read_only=True)
    attachments = TicketAttachmentSerializer(many=True, read_only=True)

    class Meta:
        model = Ticket
        fields = '__all__'
        read_only_fields = ('created_by', 'created_at', 'updated_at', 'resolved_at')

class TicketCreateSerializer(serializers.ModelSerializer):
    attachments = serializers.ListField(
        child=serializers.FileField(),
        required=False,
        write_only=True
    )

    class Meta:
        model = Ticket
        fields = ('title', 'description', 'priority', 'category', 
                 'device_type', 'device_model', 'attachments')

    def create(self, validated_data):
        attachments = validated_data.pop('attachments', [])
        ticket = Ticket.objects.create(**validated_data)
        
        for attachment in attachments:
            TicketAttachment.objects.create(
                ticket=ticket,
                file=attachment,
                uploaded_by=validated_data['created_by']
            )
        
        return ticket
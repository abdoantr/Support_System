from django.contrib import admin
from .models import ArticleCategory, Tag, KnowledgeBaseArticle, ArticleAttachment, ArticleRevision, ArticleFeedback

class ArticleAttachmentInline(admin.TabularInline):
    model = ArticleAttachment
    extra = 1
    readonly_fields = ['created_at']

class ArticleRevisionInline(admin.TabularInline):
    model = ArticleRevision
    extra = 0
    readonly_fields = ['title', 'content', 'short_description', 'tags_json', 'status', 'created_by', 'created_at']
    can_delete = False
    max_num = 0  # Don't allow adding new revisions in admin
    
    def has_add_permission(self, request, obj=None):
        return False

class ArticleFeedbackInline(admin.TabularInline):
    model = ArticleFeedback
    extra = 0
    readonly_fields = ['is_helpful', 'comment', 'user', 'created_at', 'ip_address']
    can_delete = False
    max_num = 0  # Don't allow adding new feedback in admin
    
    def has_add_permission(self, request, obj=None):
        return False

@admin.register(ArticleCategory)
class ArticleCategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'description', 'article_count', 'created_at', 'created_by']
    search_fields = ['name', 'description']
    readonly_fields = ['created_at', 'updated_at']
    list_filter = ['created_at']
    
    def article_count(self, obj):
        return obj.articles.count()
    article_count.short_description = 'Articles'

@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ['name', 'article_count']
    search_fields = ['name']
    
    def article_count(self, obj):
        # Count articles that contain this tag
        from django.db.models import Q
        return KnowledgeBaseArticle.objects.filter(tags_json__icontains=obj.name).count()
    
    article_count.short_description = 'Articles'

@admin.register(KnowledgeBaseArticle)
class KnowledgeBaseArticleAdmin(admin.ModelAdmin):
    list_display = ['title', 'category', 'status', 'visibility', 'is_featured', 'views', 'rating', 'created_by', 'updated_at']
    list_filter = ['status', 'visibility', 'is_featured', 'category', 'created_at']
    search_fields = ['title', 'short_description', 'content', 'tags_json']
    readonly_fields = ['views', 'rating', 'rating_count', 'created_at', 'updated_at', 'slug']
    fieldsets = (
        (None, {
            'fields': ('title', 'slug', 'short_description', 'content')
        }),
        ('Categorization', {
            'fields': ('category', 'tags_json', 'related_articles')
        }),
        ('Status', {
            'fields': ('status', 'visibility', 'is_featured')
        }),
        ('Statistics', {
            'fields': ('views', 'rating', 'rating_count')
        }),
        ('Metadata', {
            'fields': ('created_by', 'updated_by', 'created_at', 'updated_at')
        }),
    )
    inlines = [ArticleAttachmentInline, ArticleRevisionInline, ArticleFeedbackInline]
    
    def save_model(self, request, obj, form, change):
        if not change:  # If this is a new object
            obj.created_by = request.user
        obj.updated_by = request.user
        super().save_model(request, obj, form, change)
    
    def get_queryset(self, request):
        # Show all articles to staff, but only their own to non-staff users
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs
        return qs.filter(created_by=request.user)

@admin.register(ArticleAttachment)
class ArticleAttachmentAdmin(admin.ModelAdmin):
    list_display = ['filename', 'article', 'file_type', 'created_at']
    list_filter = ['created_at', 'file_type']
    search_fields = ['filename', 'article__title']
    readonly_fields = ['created_at']

@admin.register(ArticleRevision)
class ArticleRevisionAdmin(admin.ModelAdmin):
    list_display = ['article', 'created_by', 'created_at']
    list_filter = ['created_at', 'status']
    search_fields = ['article__title', 'title', 'content']
    readonly_fields = ['article', 'title', 'content', 'short_description', 'tags_json', 'status', 'created_by', 'created_at']
    
    def has_add_permission(self, request):
        return False  # Revisions shouldn't be created manually

@admin.register(ArticleFeedback)
class ArticleFeedbackAdmin(admin.ModelAdmin):
    list_display = ['article', 'is_helpful', 'user', 'created_at']
    list_filter = ['is_helpful', 'created_at']
    search_fields = ['article__title', 'comment']
    readonly_fields = ['article', 'is_helpful', 'user', 'comment', 'created_at', 'ip_address']
    
    def has_add_permission(self, request):
        return False  # Feedback shouldn't be created manually 
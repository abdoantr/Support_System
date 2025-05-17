from django.db import models
from django.conf import settings
from django.utils.text import slugify
import json
from django.utils import timezone

class ArticleCategory(models.Model):
    """Model for knowledge base article categories"""
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True, null=True)
    icon = models.CharField(max_length=50, default="fas fa-folder")
    color = models.CharField(max_length=50, default="#3498db")
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='created_categories'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return self.name
    
    class Meta:
        verbose_name = "Category"
        verbose_name_plural = "Categories"
        ordering = ['name']


class Tag(models.Model):
    """Model for knowledge base article tags"""
    name = models.CharField(max_length=50, unique=True)
    
    def __str__(self):
        return self.name
    
    class Meta:
        ordering = ['name']


class KnowledgeBaseArticle(models.Model):
    """Model for knowledge base articles"""
    
    class Status(models.TextChoices):
        DRAFT = 'draft', 'Draft'
        PUBLISHED = 'published', 'Published'
        ARCHIVED = 'archived', 'Archived'
    
    class Visibility(models.TextChoices):
        PUBLIC = 'public', 'Public'
        INTERNAL = 'internal', 'Internal (Staff only)'
        PRIVATE = 'private', 'Private (Selected users only)'
    
    title = models.CharField(max_length=200)
    slug = models.SlugField(max_length=250, unique=True, blank=True)
    short_description = models.CharField(max_length=255)
    content = models.TextField()
    category = models.ForeignKey(ArticleCategory, on_delete=models.SET_NULL, null=True, related_name='articles')
    tags_json = models.TextField(default='[]', blank=True)  # Store tags as JSON
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.DRAFT)
    visibility = models.CharField(max_length=20, choices=Visibility.choices, default=Visibility.PUBLIC)
    is_featured = models.BooleanField(default=False)
    views = models.PositiveIntegerField(default=0)
    rating = models.FloatField(default=0)
    rating_count = models.PositiveIntegerField(default=0)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='created_articles'
    )
    updated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='updated_articles'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    related_articles = models.ManyToManyField('self', symmetrical=False, blank=True)
    
    def __str__(self):
        return self.title
    
    def save(self, *args, **kwargs):
        # Generate slug if not provided
        if not self.slug:
            base_slug = slugify(self.title)
            slug = base_slug
            counter = 1
            while KnowledgeBaseArticle.objects.filter(slug=slug).exists():
                slug = f"{base_slug}-{counter}"
                counter += 1
            self.slug = slug
        
        # Update tag objects if tags have changed
        if self.pk:
            old_instance = KnowledgeBaseArticle.objects.get(pk=self.pk)
            if old_instance.tags_json != self.tags_json:
                self.update_tags()
        else:
            # For new articles
            self.update_tags()
        
        super().save(*args, **kwargs)
    
    def update_tags(self):
        """Update tag objects based on tags_json field"""
        try:
            tags = json.loads(self.tags_json)
            for tag_name in tags:
                Tag.objects.get_or_create(name=tag_name.lower().strip())
        except json.JSONDecodeError:
            pass  # Invalid JSON
    
    @property
    def tags(self):
        """Return list of tags from JSON field"""
        try:
            return json.loads(self.tags_json)
        except:
            return []
    
    class Meta:
        verbose_name = "Knowledge Base Article"
        verbose_name_plural = "Knowledge Base Articles"
        ordering = ['-updated_at']


class ArticleAttachment(models.Model):
    """Model for article attachments"""
    article = models.ForeignKey(KnowledgeBaseArticle, on_delete=models.CASCADE, related_name='attachments')
    file = models.FileField(upload_to='knowledge_base/attachments/%Y/%m/')
    filename = models.CharField(max_length=255, blank=True)
    file_type = models.CharField(max_length=100, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return self.filename or self.file.name
    
    def save(self, *args, **kwargs):
        if not self.filename and self.file:
            self.filename = self.file.name
        super().save(*args, **kwargs)
    
    @property
    def file_extension(self):
        """Return the file extension"""
        if self.file:
            return self.file.name.split('.')[-1].lower()
        return ''
    
    @property
    def is_image(self):
        """Check if file is an image"""
        image_extensions = ['jpg', 'jpeg', 'png', 'gif', 'webp']
        return self.file_extension in image_extensions
    
    @property
    def is_document(self):
        """Check if file is a document"""
        doc_extensions = ['pdf', 'doc', 'docx', 'xls', 'xlsx', 'ppt', 'pptx', 'txt']
        return self.file_extension in doc_extensions


class ArticleRevision(models.Model):
    """Model for article revision history"""
    article = models.ForeignKey(KnowledgeBaseArticle, on_delete=models.CASCADE, related_name='revisions')
    title = models.CharField(max_length=200)
    content = models.TextField()
    short_description = models.CharField(max_length=255)
    tags_json = models.TextField(default='[]', blank=True)
    status = models.CharField(max_length=20, choices=KnowledgeBaseArticle.Status.choices)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='article_revisions'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"Revision of {self.article.title} - {self.created_at}"
    
    class Meta:
        ordering = ['-created_at']


class ArticleFeedback(models.Model):
    """Model for article feedback"""
    article = models.ForeignKey(KnowledgeBaseArticle, on_delete=models.CASCADE, related_name='feedback')
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='article_feedback'
    )
    is_helpful = models.BooleanField()
    comment = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    ip_address = models.GenericIPAddressField(blank=True, null=True)
    
    def save(self, *args, **kwargs):
        # Update article rating when feedback is saved
        is_new = self.pk is None
        super().save(*args, **kwargs)
        
        if is_new and self.article:
            # Get total helpful feedback
            helpful_count = ArticleFeedback.objects.filter(
                article=self.article,
                is_helpful=True
            ).count()
            
            # Get total feedback
            total_count = ArticleFeedback.objects.filter(article=self.article).count()
            
            # Calculate rating (percentage of helpful feedback)
            if total_count > 0:
                rating = (helpful_count / total_count) * 5  # Scale to 5
                self.article.rating = rating
                self.article.rating_count = total_count
                self.article.save(update_fields=['rating', 'rating_count'])
    
    def __str__(self):
        return f"Feedback on {self.article.title} - {'Helpful' if self.is_helpful else 'Not Helpful'}"
    
    class Meta:
        ordering = ['-created_at'] 
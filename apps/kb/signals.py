from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from .models import KnowledgeBaseArticle, ArticleRevision

@receiver(post_save, sender=KnowledgeBaseArticle)
def create_initial_revision(sender, instance, created, **kwargs):
    """
    Create an initial revision when a new article is created
    """
    if created:
        ArticleRevision.objects.create(
            article=instance,
            title=instance.title,
            content=instance.content,
            short_description=instance.short_description,
            tags_json=instance.tags_json,
            status=instance.status,
            created_by=instance.created_by
        ) 
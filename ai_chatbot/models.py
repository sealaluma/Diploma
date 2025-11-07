from django.db import models
from users.models import CustomUser


class AIUsageWindow(models.Model):
    user = models.ForeignKey(
        CustomUser,
        on_delete=models.CASCADE,
        related_name='ai_usage_windows'
    )
    feature_type = models.CharField(
        max_length=20,
        choices=[
            ('topic_enhancement', 'Topic Enhancement'),
            ('chatbot_message', 'Chatbot Message'),
        ]
    )
    date = models.DateField()
    usage_count = models.PositiveIntegerField(default=0)

    class Meta:
        unique_together = ['user', 'feature_type', 'date']
        indexes = [
            models.Index(fields=['user', 'feature_type', 'date']),
        ]
        verbose_name = 'AI Usage Window'
        verbose_name_plural = 'AI Usage Windows'

    def __str__(self):
        return f"{self.user.email} - {self.feature_type} - {self.date} - {self.usage_count}"

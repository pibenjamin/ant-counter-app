from django.db import models
from django.contrib.auth.models import User


class UserImage(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="images")
    title = models.CharField(max_length=255, blank=True)
    species = models.CharField(max_length=255, blank=True, default="")
    image = models.ImageField(upload_to="images/")
    width = models.PositiveIntegerField(default=0)
    height = models.PositiveIntegerField(default=0)
    uploaded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-uploaded_at"]

    def __str__(self):
        return f"{self.title or self.image.name} ({self.user.username})"


class AntAnnotation(models.Model):
    image = models.ForeignKey(
        UserImage, on_delete=models.CASCADE, related_name="annotations"
    )
    x = models.FloatField()
    y = models.FloatField()
    label = models.PositiveIntegerField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["label"]

    def __str__(self):
        return f"#{self.label} ({self.x:.1f}, {self.y:.1f})"

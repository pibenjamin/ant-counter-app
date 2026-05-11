from django.db import models
from django.contrib.auth.models import User
from django.utils.translation import gettext_lazy as _


class UserImageManager(models.Manager):
    def for_user(self, user):
        if user.is_staff:
            return self.all()
        return self.filter(user=user)


class UserImage(models.Model):
    objects = UserImageManager()
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="images", verbose_name=_("utilisateur"))
    title = models.CharField(max_length=255, blank=True, verbose_name=_("titre"))
    species = models.CharField(max_length=255, blank=True, default="", verbose_name=_("espèce"))
    image = models.ImageField(upload_to="images/", verbose_name=_("image"))
    width = models.PositiveIntegerField(default=0, verbose_name=_("largeur"))
    height = models.PositiveIntegerField(default=0, verbose_name=_("hauteur"))
    uploaded_at = models.DateTimeField(auto_now_add=True, verbose_name=_("uploadé le"))

    class Meta:
        ordering = ["-uploaded_at"]
        verbose_name = _("image utilisateur")
        verbose_name_plural = _("images utilisateurs")

    def __str__(self):
        return f"{self.title or self.image.name} ({self.user.username})"


class AntAnnotation(models.Model):
    image = models.ForeignKey(
        UserImage, on_delete=models.CASCADE, related_name="annotations", verbose_name=_("image")
    )
    x = models.FloatField(verbose_name=_("coordonnée X"))
    y = models.FloatField(verbose_name=_("coordonnée Y"))
    label = models.PositiveIntegerField(verbose_name=_("étiquette"))
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_("créé le"))

    class Meta:
        ordering = ["label"]
        verbose_name = _("annotation fourmi")
        verbose_name_plural = _("annotations fourmis")

    def __str__(self):
        return f"#{self.label} ({self.x:.1f}, {self.y:.1f})"


class ModelTrainingPic(models.Model):
    source = models.ForeignKey(
        UserImage, on_delete=models.SET_NULL, null=True, blank=True, related_name="training_pics"
    )
    image = models.ImageField(upload_to="training/")
    width = models.PositiveIntegerField()
    height = models.PositiveIntegerField()
    species = models.CharField(max_length=255, blank=True, default="")
    title = models.CharField(max_length=255, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = _("image d'entraînement")
        verbose_name_plural = _("images d'entraînement")

    def __str__(self):
        return f"Training {self.title or self.image.name} ({self.width}x{self.height})"

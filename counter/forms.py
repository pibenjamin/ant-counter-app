from django import forms
from django.utils.translation import gettext_lazy as _
from .models import UserImage


class ImageUploadForm(forms.ModelForm):
    class Meta:
        model = UserImage
        fields = ("image", "title", "species")
        labels = {
            "image": _("Image"),
            "title": _("Titre"),
            "species": _("Espèce"),
        }
        widgets = {
            "image": forms.FileInput(attrs={"class": "form-control", "accept": "image/*"}),
            "title": forms.TextInput(attrs={"class": "form-control", "placeholder": _("Ex: Colonie A - 2024-03-15")}),
            "species": forms.TextInput(attrs={"class": "form-control", "placeholder": _("Ex: Messor barbarus"), "autocomplete": "off"}),
        }

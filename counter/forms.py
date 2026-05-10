from django import forms
from .models import UserImage


class ImageUploadForm(forms.ModelForm):
    class Meta:
        model = UserImage
        fields = ("image", "title", "species")
        widgets = {
            "image": forms.FileInput(attrs={"class": "form-control", "accept": "image/*"}),
            "title": forms.TextInput(attrs={"class": "form-control", "placeholder": "Ex: Colonie A - 2024-03-15"}),
            "species": forms.TextInput(attrs={"class": "form-control", "placeholder": "Ex: Messor barbarus", "autocomplete": "off"}),
        }

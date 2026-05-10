from django.contrib.auth import get_user_model
from allauth.account.forms import SignupForm
from django import forms


class AutoUsernameSignupForm(SignupForm):
    def clean_username(self):
        username = self.cleaned_data.get("username", "").strip()
        if not username:
            raise forms.ValidationError("Ce champ est requis.")
        User = get_user_model()
        base_username = username
        suffix = 1
        while User.objects.filter(username__iexact=username).exists():
            username = f"{base_username}_{suffix}"
            suffix += 1
        return username

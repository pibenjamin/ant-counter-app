from django.contrib.auth import get_user_model
from allauth.account.forms import SignupForm
from django import forms
from django.utils.translation import gettext_lazy as _


class AutoUsernameSignupForm(SignupForm):
    def clean_username(self):
        username = self.cleaned_data.get("username", "").strip()
        if not username:
            raise forms.ValidationError(_("Ce champ est requis."))
        User = get_user_model()
        base_username = username
        suffix = 1
        while User.objects.filter(username__iexact=username).exists():
            username = f"{base_username}_{suffix}"
            suffix += 1
        return username

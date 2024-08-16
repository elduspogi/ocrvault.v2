from django import forms
from django.utils.translation import gettext_lazy as _
from .models import *
from django.contrib.auth.forms import PasswordChangeForm
import re

class LoginForm(forms.Form):
    email = forms.CharField(required=True, error_messages={'required': _('Email Address is required.')})
    password = forms.CharField(required=True, error_messages={'required': _('Password is required.')})

class NewUserForm(forms.Form):
    email = forms.CharField(required=True, error_messages={'required': _('Email Address is required.')})
    name = forms.CharField(required=True, error_messages={'required': _('Full Name is required.')})

class EditUserForm(forms.Form):
    email = forms.CharField(required=True, error_messages={'required': _('Email Address is required.')})
    name = forms.CharField(required=True, error_messages={'required': _('Full Name is required.')})

class PasswordChangeForm(PasswordChangeForm):
    old_password = forms.CharField(required=True, error_messages={'required': _('Old Password is required.')})
    new_password1 = forms.CharField(required=True, error_messages={'required': _('New Password is required.')})
    new_password2 = forms.CharField(required=True, error_messages={'required': _('Confirming Password is required.')})

    def clean_new_password1(self):
        new_password1 = self.cleaned_data.get('new_password1')

        if len(new_password1) < 8:
            self.add_error('new_password1', _('Password must be at least 8 characters long.'))
        elif not re.search(r'\d', new_password1):
            self.add_error('new_password1', _('Password must contain at least 1 number.'))
        elif not re.search(r'[A-Z]', new_password1):
            self.add_error('new_password1', _('Password must contain at least 1 capital letter.'))

        return new_password1

    def clean_new_password2(self):
        new_password1 = self.cleaned_data.get('new_password1')
        new_password2 = self.cleaned_data.get('new_password2')

        if new_password1 and new_password2 and new_password1 != new_password2:
            self.add_error('new_password1', _('Passwords do not match.'))

        return new_password2
    
class ForgotPasswordForm(forms.Form):
    email = forms.CharField(required=True, error_messages={'required': _('Email Address is required.')})
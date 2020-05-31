from django import forms
from .models import User, Message, Metadata
import django.utils.timezone as timezone
from multi_email_field.forms import MultiEmailField
from django.utils.translation import gettext as _


class UserForm(forms.ModelForm):
    username = forms.CharField(label='username', widget=forms.TextInput)
    password = forms.CharField(label='password', widget=forms.PasswordInput)
    password2 = forms.CharField(label='repeat password, please', widget=forms.PasswordInput)

    class Meta:
        model = User
        fields = ['username', 'password', 'password2']

    def clean_password2(self):
        cd = self.cleaned_data
        if cd['password'] != cd['password2']:
            raise forms.ValidationError('password don\'t match')

        return cd['password']


class LoginForm(forms.ModelForm):
    username = forms.CharField(label='username', widget=forms.TextInput)
    password = forms.CharField(label='password', widget=forms.PasswordInput)

    class Meta:
        model = User
        fields = ['username', 'password']


class DateTimeInput(forms.DateTimeInput):
    input_type = "datetime-local"

    def __init__(self, **kwargs):
        kwargs["format"] = "%Y-%m-%dT%H:%M"
        super().__init__(**kwargs)


class MessageForm(forms.ModelForm):
    receivers = forms.ModelMultipleChoiceField(User.objects, required=False)
    title = forms.CharField(required=False)
    text = forms.Textarea()
    send_date = forms.DateTimeField(required=False, widget=DateTimeInput,
                                    input_formats=["%Y-%m-%dT%H:%M", "%Y-%m-%d %H:%M"])
    emails = MultiEmailField(required=False)
    #file_field = forms.FileField(required=False, widget=forms.ClearableFileInput(attrs={'multiple': True}))

    class Meta:
        model = Message
        fields = ['receivers', 'emails', 'title', 'text', 'send_date']

    def clean_send_date(self):
        date = self.cleaned_data.get('send_date')
        if date:
            if date < timezone.now():
                raise forms.ValidationError(_('Invalid value: %(value)s'),
                        params={'value': date},
                    )
        return date
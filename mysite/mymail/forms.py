from django import forms
from .models import User, Message, Metadata
import django.utils.timezone as timezone
from multi_email_field.forms import MultiEmailField
from django.utils.translation import gettext as _


class DateTimeInput(forms.DateTimeInput):
    input_type = "datetime-local"

    def __init__(self, **kwargs):
        kwargs["format"] = "%Y-%m-%dT%H:%M"
        super().__init__(**kwargs)


class MessageForm(forms.ModelForm):
    receivers = forms.ModelMultipleChoiceField(User.objects, required=False,)
    title = forms.CharField(required=False)
    text = forms.Textarea()
    send_date = forms.DateTimeField(required=False, widget=DateTimeInput,
                                    input_formats=["%Y-%m-%dT%H:%M", "%Y-%m-%d %H:%M"])
    emails = MultiEmailField(required=False)
    # file_field = forms.FileField(required=False, widget=forms.ClearableFileInput(attrs={'multiple': True}))

    def __init__(self, *args, **kwargs):
        super(MessageForm, self).__init__(*args, **kwargs)
        for visible in self.visible_fields():
            visible.field.widget.attrs['class'] = 'form-control'
        self.fields["emails"].widget.attrs['rows'] = "2"
        self.fields["text"].widget.attrs['rows'] = "2"

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

    def clean_receivers(self):
        receivers = self.cleaned_data.get('receivers')
        emails = self.cleaned_data.get('emails')
        if not receivers and not emails:
            raise forms.ValidationError(_('Error: No receivers or emails'))
        return receivers
from django import forms
from .models import Connection


class ConnectionForm(forms.ModelForm):
    password = forms.CharField(widget=forms.PasswordInput)

    class Meta:
        model = Connection
        fields = ('host', 'username', 'password')

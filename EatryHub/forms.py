from django import forms
from django.contrib.auth import authenticate
from django.contrib.auth.forms import UsernameField

class LoginForm(forms.Form):
    username = UsernameField(
        label='ユーザー名',
        widget=forms.TextInput(attrs={'placeholder': 'ユーザー名', 'autofocus': True}),
    )
    password = forms.CharField(
        label='パスワード',
        strip=False,
        widget=forms.PasswordInput(attrs={'placeholder': 'パスワード'}),
    )

    def __init__(self, *args, **kwargs):
        self.request = kwargs.pop('request', None)
        super().__init__(*args, **kwargs)
        self.user_cache = None

    def clean(self):
        data = super().clean()
        user = authenticate(self.request, username=data.get('username'), password=data.get('password'))
        if user is None:
            raise forms.ValidationError("正しいユーザー名とパスワードを入力してください")
        self.user_cache = user
        return data

    def get_user(self):
        return self.user_cache
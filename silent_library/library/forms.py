from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import User, Book, Review
import re
from django.core.exceptions import ValidationError


class CharacterVarietyValidator:
    def __call__(self, password):
        if not re.search(r'[A-Z]', password):
            raise ValidationError("Password must contain at least one uppercase letter.", code='password_no_upper')
        if not re.search(r'[a-z]', password):
            raise ValidationError("Password must contain at least one lowercase letter.", code='password_no_lower')
        if not re.search(r'\d', password):
            raise ValidationError("Password must contain at least one digit.", code='password_no_digit')
        if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
            raise ValidationError("Password must contain at least one symbol.", code='password_no_symbol')

    def get_help_text(self):
        return "Your password must contain at least one uppercase letter, one lowercase letter, one digit, and one symbol."


class UserRegistrationForm(UserCreationForm):
    class Meta(UserCreationForm.Meta):
        model = User
        fields = ('username', 'email', 'first_name', 'last_name')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['password1'].help_text = "Your password must contain at least one uppercase letter, one lowercase letter, one digit, and one symbol."
        self.fields['password2'].help_text = "Enter the same password as before, for verification."
        self.fields['password1'].validators.append(CharacterVarietyValidator())
        for field_name, field in self.fields.items():
            field.widget.attrs['class'] = 'form-control'


class UserLoginForm(forms.Form):
    username = forms.CharField()
    password = forms.CharField(widget=forms.PasswordInput)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field_name, field in self.fields.items():
            field.widget.attrs['class'] = 'form-control'


class UserEditForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ('first_name', 'last_name')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field_name, field in self.fields.items():
            field.widget.attrs['class'] = 'form-control'
            field.widget.attrs['required'] = True


class UserEditUsernameEmailForm(forms.ModelForm):
    current_password = forms.CharField(widget=forms.PasswordInput, label="Current Password")

    class Meta:
        model = User
        fields = ('username', 'email')

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        for field_name, field in self.fields.items():
            field.widget.attrs['class'] = 'form-control'
            field.widget.attrs['required'] = True

    def clean_current_password(self):
        current_password = self.cleaned_data.get('current_password')
        if not self.user.check_password(current_password):
            raise forms.ValidationError("Incorrect password.")
        return current_password


class UserEditPasswordForm(forms.Form):
    current_password = forms.CharField(widget=forms.PasswordInput, label="Current Password")
    new_password = forms.CharField(widget=forms.PasswordInput, label="New Password", help_text="Your password must contain at least one uppercase letter, one lowercase letter, one digit, and one symbol.")
    confirm_new_password = forms.CharField(widget=forms.PasswordInput, label="Confirm New Password")

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        self.fields['new_password'].validators.append(CharacterVarietyValidator())
        for field_name, field in self.fields.items():
            field.widget.attrs['class'] = 'form-control'
            field.widget.attrs['required'] = True

    def clean_current_password(self):
        current_password = self.cleaned_data.get('current_password')
        if not self.user.check_password(current_password):
            raise forms.ValidationError("Incorrect password.")
        return current_password

    def clean(self):
        cleaned_data = super().clean()
        new_password = cleaned_data.get("new_password")
        confirm_new_password = cleaned_data.get("confirm_new_password")

        if new_password and new_password != confirm_new_password:
            self.add_error('confirm_new_password', "Passwords don't match.")

        return cleaned_data

    def save(self, commit=True):
        password = self.cleaned_data["new_password"]
        self.user.set_password(password)
        if commit:
            self.user.save()
        return self.user


class BookForm(forms.ModelForm):
    class Meta:
        model = Book
        fields = '__all__'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field_name, field in self.fields.items():
            field.widget.attrs['class'] = 'form-control'


class ReviewForm(forms.ModelForm):
    class Meta:
        model = Review
        fields = ['review_text', 'rating']

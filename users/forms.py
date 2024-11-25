from allauth.account.forms import SignupForm
from django.utils.safestring import mark_safe
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Submit
from django import forms

from .models import verify_birth_date


class UserSignupForm(SignupForm):
    first_name = forms.CharField(max_length=30, label='Primeiro Nome')
    last_name = forms.CharField(max_length=30, label='Último Nome')

    birth_date = forms.DateField(
        widget=forms.DateInput(attrs={'type': 'date'}),  # Usando um input de data
        validators=[verify_birth_date]
    )

    tos_accept = forms.BooleanField(
        label=mark_safe(f'Você concorda com nossos <a href="/tos/" target="_blank">Termos de Serviço</a>?'),
        required=True
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.layout = Layout(
            'username',
            'first_name',
            'last_name',
            'birth_date',
            'email',
            'password1',
            'password2',
            'tos_accept',
            Submit('submit', 'Registrar', css_class='btn btn-primary')
        )

    def clean_tos_accept(self):
        tos_accept = self.cleaned_data.get('tos_accept')
        if not tos_accept:
            raise forms.ValidationError('Você precisa aceitar os Termos de Serviço para se registrar.')
        return tos_accept

    def clean_birth_date(self):
        birth_date = self.cleaned_data['birth_date']
        verify_birth_date(birth_date)
        return birth_date

    def save(self, request):
        if not self.cleaned_data.get('tos_accept'):
            raise forms.ValidationError("Você precisa aceitar os Termos de Serviço.")

        if not self.cleaned_data.get('birth_date'):
            raise forms.ValidationError("Você precisa oferecer uma data de nascimento correta.")

        user = super().save(request)
        user.first_name = self.cleaned_data.get('first_name')
        user.last_name = self.cleaned_data.get('last_name')
        user.birth_date = self.cleaned_data.get('birth_date')
        user.tos_accept = self.cleaned_data.get('tos_accept')
        user.save()
        return user

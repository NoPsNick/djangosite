import re

from allauth.account.forms import SignupForm
from django.utils.safestring import mark_safe
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Row, Column, Submit
from django import forms


class UserSignupForm(SignupForm):
    first_name = forms.CharField(max_length=30, label='Primeiro Nome')
    last_name = forms.CharField(max_length=30, label='Último Nome')
    doc_type = forms.ChoiceField(
        choices=[('CPF', 'CPF'), ('CNPJ', 'CNPJ')],
        label='Tipo do Documento'
    )
    doc_number = forms.CharField(max_length=250, label='Número do Documento')

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
            Row(
                Column('doc_type', css_class='col-md-4'),
                Column('doc_number', css_class='col-md-8'),
                css_class='row g-3'
            ),
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

    def clean(self):
        cleaned_data = super().clean()
        doc_type = cleaned_data.get('doc_type')
        doc_number = cleaned_data.get('doc_number')

        if doc_type and doc_number:
            # Add document validation logic here
            if doc_type == 'CPF' and not self.is_valid_cpf(doc_number):
                self.add_error('doc_number', 'Número de CPF inválido.')
            elif doc_type == 'CNPJ' and not self.is_valid_cnpj(doc_number):
                self.add_error('doc_number', 'Número de CNPJ inválido.')
        else:
            self.add_error('doc_number', 'Você precisa fornecer um documento válido.')

        return cleaned_data

    @staticmethod
    def is_valid_cpf(cpf):
        cpf = re.sub(r'\D', '', cpf)  # Remove caracteres não numéricos

        if len(cpf) != 11 or cpf == cpf[0] * 11:
            return False

        def calculate_digit(digits):
            total = sum(int(d) * w for d, w in zip(digits, range(len(digits) + 1, 1, -1)))
            remainder = total % 11
            return '0' if remainder < 2 else str(11 - remainder)

        base_digits = cpf[:9]
        check_digits = cpf[9:]

        first_digit = calculate_digit(base_digits)
        second_digit = calculate_digit(base_digits + first_digit)

        return check_digits == first_digit + second_digit

    @staticmethod
    def is_valid_cnpj(cnpj):
        cnpj = re.sub(r'\D', '', cnpj)  # Remove caracteres não numéricos

        if len(cnpj) != 14 or cnpj == cnpj[0] * 14:
            return False

        def calculate_digit(digits, weights):
            total = sum(int(d) * w for d, w in zip(digits, weights))
            remainder = total % 11
            return '0' if remainder < 2 else str(11 - remainder)

        base_digits = cnpj[:12]
        check_digits = cnpj[12:]

        first_digit = calculate_digit(base_digits, list(range(5, 1, -1)) + list(range(9, 5, -1)))
        second_digit = calculate_digit(base_digits + first_digit, list(range(6, 1, -1)) + list(range(9, 6, -1)))

        return check_digits == first_digit + second_digit

    def save(self, request):
        if not self.cleaned_data.get('tos_accept'):
            raise forms.ValidationError("Você precisa aceitar os Termos de Serviço.")

        user = super().save(request)
        user.first_name = self.cleaned_data.get('first_name')
        user.last_name = self.cleaned_data.get('last_name')
        user.doc_type = self.cleaned_data.get('doc_type')
        user.doc_number = self.cleaned_data.get('doc_number')
        user.tos_accept = self.cleaned_data.get('tos_accept')
        user.save()
        return user

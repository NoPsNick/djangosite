from django import forms

from .models import PaymentMethod


class PaymentForm(forms.Form):
    payment_method = forms.ModelChoiceField(
        label = "Método de Pagamento",
        queryset=PaymentMethod.objects.all(),
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    promo_codes = forms.CharField(
        label = "Cupons",
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Cupons (Separados por '
                                                                              'Vírgula)'})
    )

    def clean_promo_codes(self):
        codes = self.cleaned_data.get('promo_codes')
        if codes:
            return [code.strip() for code in codes.split(',')]
        return []

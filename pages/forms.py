from django import forms
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Fieldset, Layout, Submit, Field, Div
from django.core.exceptions import ValidationError


# class EnderecoCreateForm(forms.ModelForm):
#     class Meta:
#         model = Address
#         fields = [
#             "postal_code",
#             "rua",
#             "number",
#             "complement",
#             "district",
#             "state",
#             "city",
#         ]
#
#     def __init__(self, *args, **kwargs):
#         super().__init__(*args, **kwargs)
#         self.helper = FormHelper()
#         self.helper.form_method = "post"
#         self.helper.form_action = "."
#         self.helper.add_input(
#             Submit(
#                 "submit",
#                 "Adicionar endereço",
#                 css_class="btn btn-success btn-lg btn-block",
#             )
#         )
#         self.helper.layout = Layout(
#             Fieldset(
#                 "",
#                 Div(
#                     Field("postal_code", onchange="getAddress()", wrapper_class="col"),
#                     Field("state", wrapper_class="col"),
#                     Field("city", wrapper_class="col"),
#                     css_class="row",
#                 ),
#                 Div(
#                     Field("rua", wrapper_class="col"),
#                     Field("district", wrapper_class="col"),
#                     css_class="row",
#                 ),
#                 Div(
#                     Field("number", wrapper_class="col"),
#                     Field("complement", wrapper_class="col"),
#                     css_class="row",
#                 ),
#                 css_class="border-bottom mb-3",
#             )
#         )
#
#     def clean_postal_code(self):
#         postal_code = self.cleaned_data.get("postal_code").strip()
#         if not postal_code:
#             raise ValidationError("O campo CEP não pode estar vazio.")
#         return postal_code
#
#     def clean_rua(self):
#         rua = self.cleaned_data.get("rua").strip()
#         if not rua:
#             raise ValidationError("O campo Rua não pode estar vazio.")
#         return rua
#
#     def clean_number(self):
#         number = self.cleaned_data.get("number").strip()
#         if not number:
#             raise ValidationError("O campo Número não pode estar vazio.")
#         return number
#
#     def clean_distric(self):
#         distric = self.cleaned_data.get("distric").strip()
#         if not distric:
#             raise ValidationError("O campo Bairro não pode estar vazio.")
#         return distric
#
#     def clean_state(self):
#         state = self.cleaned_data.get("state").strip()
#         if not state:
#             raise ValidationError("O campo Estado não pode estar vazio.")
#         return state
#
#     def clean_city(self):
#         city = self.cleaned_data.get("city").strip()
#         if not city:
#             raise ValidationError("O campo Cidade não pode estar vazio.")
#         return city
#
#
# class TelefoneCreateForm(forms.ModelForm):
#     class Meta:
#         model = PhoneNumber
#         fields = [
#             "number",
#         ]
#
#     def __init__(self, *args, **kwargs):
#         self.user = kwargs.pop('user', None)
#         super().__init__(*args, **kwargs)
#         self.helper = FormHelper()
#         self.helper.form_method = "post"
#         self.helper.form_action = "."
#         self.helper.add_input(
#             Submit(
#                 "submit",
#                 "Adicionar telefone",
#                 css_class="btn btn-success btn-lg btn-block",
#             )
#         )
#         self.helper.layout = Layout(
#             Fieldset(
#                 "",
#                 Field("number", wrapper_class="col"),
#             )
#         )
#
#     def clean_number(self):
#         number = self.cleaned_data.get("number").strip()
#         if not number:
#             raise ValidationError("O campo Número não pode estar vazio.")
#         return number

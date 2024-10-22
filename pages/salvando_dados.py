
# class UserAddressList(ListView):
#     template_name = "enderecos.html"
#     model = Address
#     context_object_name = "endereco_list"
#
#     def get_queryset(self):
#         # Retrieve addresses from cache
#         addresses = get_user_addresses(self.request.user)
#
#         return addresses
#
#
# @method_decorator(strict_rate_limit(url_names=['pages:address_add']), name='dispatch')
# class UserAddressAdd(CreateView):
#     model = Address
#     form_class = EnderecoCreateForm
#     template_name = "endereco_add.html"
#
#     def form_valid(self, form):
#         form.instance.user = self.request.user
#         if form.instance.user.verify_address():
#             endereco = form.save()
#
#             # Define como selecionado se o usuário ainda não tiver um endereço selecionado
#             if not self.request.user.address:
#                 endereco.set_address_as_selected()
#
#             messages.success(self.request, 'Endereço criado com sucesso.')
#             return redirect(reverse("pages:address_list"))
#         else:
#             messages.warning(self.request, 'Você possuí o número máximo de endereços criados.')
#             return redirect(reverse("pages:address_list"))
#
#
# @method_decorator(strict_rate_limit(url_names=['pages:address_update']), name='dispatch')
# class UserAddressUpdate(UserPassesTestMixin, UpdateView):
#     model = Address
#     fields = [
#         "postal_code",
#         "rua",
#         "number",
#         "complement",
#         "district",
#         "state",
#         "city",
#         "selected"
#     ]
#     template_name = "endereco_update.html"
#
#     def test_func(self):
#         """Check if the current user owns the address."""
#         address = self.get_object()
#         return address.user == self.request.user
#
#     def handle_no_permission(self):
#         """Return a 403 Forbidden"""
#         response = TemplateResponse(self.request, '403.html', status=403)
#         return response
#
#     def form_valid(self, form):
#         """Custom validation to handle 'selected' status and ensure correct address."""
#         user = self.request.user
#         addresses = get_user_addresses(user)
#         filtered_address = [address for address in addresses if address['id'] == form.instance.id]
#
#         if filtered_address:
#             address = filtered_address[0]
#             if address['selected']:
#                 messages.warning(self.request, 'Não é possível alterar o seu endereço principal.')
#                 return redirect(reverse("pages:address_list"))
#
#             if form.instance.selected and not address['selected']:
#                 form.instance.set_address_as_selected()
#         else:
#             messages.warning(self.request, "Ocorreu um erro ao tentar encontrar o endereço")
#             return redirect(reverse("pages:address_list"))
#
#         form.save()
#         messages.success(self.request, 'Endereço alterado com sucesso.')
#         return redirect(reverse("pages:address_list"))
#
#
# @method_decorator(strict_rate_limit(url_names=['pages:address_delete']), name='dispatch')
# class UserAddressDelete(UserPassesTestMixin, DeleteView):
#     model = Address
#
#     def test_func(self):
#         """Check if the current user owns the address."""
#         address = self.get_object()
#         return address.user == self.request.user
#
#     def handle_no_permission(self):
#         """Return a 403 Forbidden"""
#         response = TemplateResponse(self.request, '403.html', status=403)
#         return response
#
#     def get_success_url(self):
#         """Return the success URL after deleting an address."""
#         return reverse_lazy('pages:address_list')
#
#
# class UserPhoneNumberList(ListView):
#     template_name = "telefones.html"
#     model = PhoneNumber
#     context_object_name = "telefone_list"
#
#     def get_queryset(self):
#         # Retrieve phone_numbers from cache
#         phone_numbers = get_user_numbers(self.request.user)
#
#         return phone_numbers
#
#
# @method_decorator(strict_rate_limit(url_names=['pages:phone_add']), name='dispatch')
# class UserPhoneNumberAdd(CreateView):
#     model = PhoneNumber
#     form_class = TelefoneCreateForm
#     template_name = "telefone_add.html"
#
#     def form_valid(self, form):
#         form.instance.user = self.request.user
#
#         if form.instance.user.verify_phone_number():
#             phone_number = form.save()
#
#             # Define como selecionado se o usuário ainda não tiver um endereço selecionado
#             if not self.request.user.phone_number:
#                 phone_number.set_phone_number_as_selected()
#
#             messages.success(self.request, 'Telefone criado com sucesso.')
#             return redirect(reverse("pages:phone_list"))
#         else:
#             messages.warning(self.request, 'Você possuí o número máximo de telefones criados.')
#             return redirect(reverse("pages:phone_list"))
#
#
# @method_decorator(strict_rate_limit(url_names=['pages:phone_update']), name='dispatch')
# class UserPhoneNumberUpdate(UserPassesTestMixin, UpdateView):
#     model = PhoneNumber
#     fields = [
#         "number",
#         "selected"
#     ]
#     template_name = "telefone_update.html"
#
#     def test_func(self):
#         """Check if the current user owns the phone number."""
#         phone_number = self.get_object()
#         return phone_number.user == self.request.user
#
#     def handle_no_permission(self):
#         """Return a 403 Forbidden"""
#         response = TemplateResponse(self.request, '403.html', status=403)
#         return response
#
#     def form_valid(self, form):
#         user = self.request.user
#         phone_numbers = get_user_numbers(user)
#         filtered_number = [phone for phone in phone_numbers if phone['id'] == form.instance.id]
#
#         # Verifica se há o telefone
#         if filtered_number:
#             number = filtered_number[0]
#             # Verifica se o telefone está selecionado e se é o principal
#             if number['selected']:
#                 messages.warning(self.request, 'Não é possível alterar o seu telefone principal.')
#                 return redirect(reverse("pages:phone_list"))
#
#             # Atualiza o telefone selecionado
#             if form.instance.selected and not number['selected']:
#                 form.instance.set_phone_number_as_selected()
#
#         form.save()
#         messages.success(self.request, 'Telefone alterado com sucesso.')
#         return redirect(reverse("pages:phone_list"))
#
#
# @method_decorator(strict_rate_limit(url_names=['pages:phone_delete']), name='dispatch')
# class UserPhoneNumberDelete(UserPassesTestMixin, DeleteView):
#     model = PhoneNumber
#
#     def test_func(self):
#         """Check if the current user owns the phone number."""
#         phone_number = self.get_object()
#         return phone_number.user == self.request.user
#
#     def handle_no_permission(self):
#         """Return a 403 Forbidden"""
#         response = TemplateResponse(self.request, '403.html', status=403)
#         return response
#
#     def get_success_url(self):
#         """Return the success URL after deleting a phone number."""
#         return reverse_lazy('pages:phone_list')

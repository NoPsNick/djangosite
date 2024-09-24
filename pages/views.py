from django.contrib.auth.mixins import UserPassesTestMixin
from django.views.generic.edit import CreateView, UpdateView, DeleteView
from django.shortcuts import redirect
from django.urls import reverse, reverse_lazy
from django.contrib import messages
from django.views.generic import ListView, TemplateView
from django.core.cache import cache
from django.utils.decorators import method_decorator
from django.core.exceptions import PermissionDenied
from django.template.response import TemplateResponse

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, viewsets
from rest_framework.throttling import UserRateThrottle
from rest_framework.permissions import IsAuthenticated

from legaldocs.models import TermOfService, PrivacyPolicy, ReturnPolicy
from users.models import Address, PhoneNumber
from .forms import EnderecoCreateForm, TelefoneCreateForm
from .decorators import restrict_to_server, strict_rate_limit
from .services import get_user_data, get_abouts, get_user_addresses, get_user_numbers, get_promotions
from .serializers import AddressSerializer, PhoneNumberSerializer



# Create your views here.
class HomePageView(TemplateView):
    template_name = "home.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        promotions = get_promotions()
        context['promotions'] = promotions
        return context


class AboutPageView(TemplateView):
    template_name = "about.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        about_list = get_abouts()

        context['about_list'] = about_list
        return context


class ProfilePageView(TemplateView):
    template_name = "profile.html"

    def get_context_data(self, user_id, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user

        if not user.is_authenticated:
            raise PermissionDenied("You must be logged in to view this profile.")

        # Check if the user is trying to access their own profile
        if user.id != user_id and not user.is_staff:
            raise PermissionDenied("You do not have permission to view this profile.")

        # Fetch user data from cache or database
        user_data = get_user_data(user, user_id)

        context['user_data'] = user_data
        return context


class UserAddressList(ListView):
    template_name = "enderecos.html"
    model = Address
    context_object_name = "endereco_list"

    def get_queryset(self):
        # Retrieve addresses from cache
        addresses = get_user_addresses(self.request.user)

        return addresses


@method_decorator(strict_rate_limit(url_names=['pages:address_add']), name='dispatch')
class UserAddressAdd(CreateView):
    model = Address
    form_class = EnderecoCreateForm
    template_name = "endereco_add.html"

    def form_valid(self, form):
        form.instance.user = self.request.user
        if form.instance.user.verify_address():
            endereco = form.save()

            # Define como selecionado se o usuário ainda não tiver um endereço selecionado
            if not self.request.user.address:
                endereco.set_address_as_selected()

            messages.success(self.request, 'Endereço criado com sucesso.')
            return redirect(reverse("pages:address_list"))
        else:
            messages.warning(self.request, 'Você possuí o número máximo de endereços criados.')
            return redirect(reverse("pages:address_list"))


@method_decorator(strict_rate_limit(url_names=['pages:address_update']), name='dispatch')
class UserAddressUpdate(UserPassesTestMixin, UpdateView):
    model = Address
    fields = [
        "postal_code",
        "rua",
        "number",
        "complement",
        "district",
        "state",
        "city",
        "selected"
    ]
    template_name = "endereco_update.html"

    def test_func(self):
        """Check if the current user owns the address."""
        address = self.get_object()
        return address.user == self.request.user

    def handle_no_permission(self):
        """Return a 403 Forbidden"""
        response = TemplateResponse(self.request, '403.html', status=403)
        return response

    def form_valid(self, form):
        """Custom validation to handle 'selecionado' status and ensure correct address."""
        user = self.request.user
        addresses = get_user_addresses(user)
        filtered_address = [address for address in addresses if address.id == form.instance.id]

        if filtered_address:
            address = filtered_address[0]
            if address.selected:
                messages.warning(self.request, 'Não é possível alterar o seu endereço principal.')
                return redirect(reverse("pages:address_list"))

            if form.instance.selected and not address.selected:
                form.instance.set_address_as_selected()
        else:
            messages.warning(self.request, "Ocorreu um erro ao tentar encontrar o endereço")
            return redirect(reverse("pages:address_list"))

        form.save()
        messages.success(self.request, 'Endereço alterado com sucesso.')
        return redirect(reverse("pages:address_list"))


@method_decorator(strict_rate_limit(url_names=['pages:address_delete']), name='dispatch')
class UserAddressDelete(UserPassesTestMixin, DeleteView):
    model = Address

    def test_func(self):
        """Check if the current user owns the address."""
        address = self.get_object()
        return address.user == self.request.user

    def handle_no_permission(self):
        """Return a 403 Forbidden"""
        response = TemplateResponse(self.request, '403.html', status=403)
        return response

    def get_success_url(self):
        """Return the success URL after deleting an address."""
        return reverse_lazy('pages:address_list')


class UserPhoneNumberList(ListView):
    template_name = "telefones.html"
    model = PhoneNumber
    context_object_name = "telefone_list"

    def get_queryset(self):
        # Retrieve phone_numbers from cache
        phone_numbers = get_user_numbers(self.request.user)

        return phone_numbers


@method_decorator(strict_rate_limit(url_names=['pages:phone_add']), name='dispatch')
class UserPhoneNumberAdd(CreateView):
    model = PhoneNumber
    form_class = TelefoneCreateForm
    template_name = "telefone_add.html"

    def form_valid(self, form):
        form.instance.user = self.request.user

        if form.instance.user.verify_phone_number():
            phone_number = form.save()

            # Define como selecionado se o usuário ainda não tiver um endereço selecionado
            if not self.request.user.phone_number:
                phone_number.set_phone_number_as_selected()

            messages.success(self.request, 'Telefone criado com sucesso.')
            return redirect(reverse("pages:phone_list"))
        else:
            messages.warning(self.request, 'Você possuí o número máximo de telefones criados.')
            return redirect(reverse("pages:phone_list"))


@method_decorator(strict_rate_limit(url_names=['pages:phone_update']), name='dispatch')
class UserPhoneNumberUpdate(UserPassesTestMixin, UpdateView):
    model = PhoneNumber
    fields = [
        "number",
        "selected"
    ]
    template_name = "telefone_update.html"

    def test_func(self):
        """Check if the current user owns the phone number."""
        phone_number = self.get_object()
        return phone_number.user == self.request.user

    def handle_no_permission(self):
        """Return a 403 Forbidden"""
        response = TemplateResponse(self.request, '403.html', status=403)
        return response

    def form_valid(self, form):
        user = self.request.user
        phone_numbers = get_user_numbers(user)
        filtered_number = [phone for phone in phone_numbers if phone.id == form.instance.id]

        # Verifica se há o telefone
        if filtered_number:
            number = filtered_number[0]
            # Verifica se o telefone está selecionado e se é o principal
            if number.selected:
                messages.warning(self.request, 'Não é possível alterar o seu telefone principal.')
                return redirect(reverse("pages:phone_list"))

            # Atualiza o telefone selecionado
            if form.instance.selected and not number.selected:
                form.instance.set_phone_number_as_selected()

        form.save()
        messages.success(self.request, 'Telefone alterado com sucesso.')
        return redirect(reverse("pages:phone_list"))


@method_decorator(strict_rate_limit(url_names=['pages:phone_delete']), name='dispatch')
class UserPhoneNumberDelete(UserPassesTestMixin, DeleteView):
    model = PhoneNumber

    def test_func(self):
        """Check if the current user owns the phone number."""
        phone_number = self.get_object()
        return phone_number.user == self.request.user

    def handle_no_permission(self):
        """Return a 403 Forbidden"""
        response = TemplateResponse(self.request, '403.html', status=403)
        return response

    def get_success_url(self):
        """Return the success URL after deleting a phone number."""
        return reverse_lazy('pages:phone_list')


class LegalInfos(TemplateView):
    template_name = 'legal_infos.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        terms_of_service = TermOfService.objects.get_terms_of_service()
        privacy_policies = PrivacyPolicy.objects.get_privacy_policies()
        return_policies = ReturnPolicy.objects.get_return_policies()

        context['terms_of_service'] = terms_of_service
        context['privacy_policies'] = privacy_policies
        context['return_policies'] = return_policies

        return context


@method_decorator(restrict_to_server, name='dispatch')
class InternalUserViewSet(viewsets.ViewSet):
    permission_classes = [IsAuthenticated]

    def list(self, request):
        try:
            user_data = get_user_data(request.user, request.user)
            return Response(user_data)
        except ValueError:
            return Response({"detail": "User not found"}, status=404)


@method_decorator(restrict_to_server, name='dispatch')
class AddressViewSet(viewsets.ModelViewSet):
    serializer_class = AddressSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        addresses = get_user_addresses(user)
        return addresses

    def perform_create(self, serializer):
        instance = serializer.save(user=self.request.user)
        cache_key = f"user_{instance.user.id}_addresses"
        cache.delete(cache_key)

    def perform_update(self, serializer):
        instance = serializer.save()
        cache_key = f"user_{instance.user.id}_addresses"
        cache.delete(cache_key)

    def perform_destroy(self, instance):
        user_id = instance.user.id
        instance.delete()
        cache_key = f"user_{user_id}_addresses"
        cache.delete(cache_key)


@method_decorator(restrict_to_server, name='dispatch')
class PhoneNumberViewSet(viewsets.ModelViewSet):
    serializer_class = PhoneNumberSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        phone_numbers = get_user_numbers(user)
        return phone_numbers

    def perform_create(self, serializer):
        instance = serializer.save(user=self.request.user)
        cache_key = f"user_{instance.user.id}_phone_numbers"
        cache.delete(cache_key)

    def perform_update(self, serializer):
        instance = serializer.save()
        cache_key = f"user_{instance.user.id}_phone_numbers"
        cache.delete(cache_key)

    def perform_destroy(self, instance):
        user_id = instance.user.id
        instance.delete()
        cache_key = f"user_{user_id}_phone_numbers"
        cache.delete(cache_key)


@method_decorator(restrict_to_server, name='dispatch')
class AboutAPIView(APIView):
    throttle_classes = [UserRateThrottle]

    def get(self, request, *args, **kwargs):
        # Tenta obter os dados do cache
        abouts = get_abouts()

        return Response(abouts, status=status.HTTP_200_OK)

from django.db.models import Q, Prefetch
from django.shortcuts import redirect
from django.urls import reverse_lazy, reverse
from django.utils.decorators import method_decorator
from django.views import View
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import ValidationError
from django.core.paginator import Paginator
from django.contrib import messages
from django.views.generic import TemplateView, FormView
from django.views.decorators.http import require_POST

from payments.forms import PaymentForm
from payments.services import PaymentService
from products.models import Promotion
from .models import Order, Item
from cart.services import get_cart_items, save_cart
from .services import create_order
from pages.decorators import strict_rate_limit


@method_decorator(strict_rate_limit(url_names=['orders:create_order']), name='dispatch')
class CreateOrderView(LoginRequiredMixin, View):

    @method_decorator(require_POST)
    def post(self, request, *args, **kwargs):
        # Get the cart items
        cart_items, total_price = get_cart_items(request)

        if not cart_items:
            messages.error(request, "Seu carrinho está vázio!")
            return redirect('cart:detail')

        # Prepare the items data for the order
        items_data = [{'slug': item['product']['slug'], 'quantity': item['quantity']} for item in cart_items]

        try:
            # Call the create_order function
            order = create_order(user=request.user, items_data=items_data)
            response = redirect(reverse('orders:order_detail', kwargs={'order_id': order.id}))
            save_cart(response, {}) # Set the cart with an empty dict(clear the cart items)
            messages.success(request, "Pedido criado com sucesso!")
            return response
        except ValidationError as e:
            messages.error(request, str(e))
            return redirect(reverse('cart:detail'))

    @staticmethod
    def update_promotions(products):
        for product in products:
            promotions = getattr(product, 'promotions', []).exclude(status=Promotion.EXPIRADO)
            for promotion in promotions:
                promotion.save()


@method_decorator(strict_rate_limit(url_names=['orders:order_list']), name='dispatch')
class UserOrderListView(LoginRequiredMixin, TemplateView):
    template_name = 'orders/order_list.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        search_query = self.request.GET.get('search')

        if self.request.user.is_staff:
            # Use select_related for foreign keys and prefetch_related for reverse relations
            orders_adm = Order.objects.select_related('customer').prefetch_related(
                Prefetch('items', queryset=Item.objects.select_related('product__category', 'product__role_type',
                                                                       'product__stock')),
            ).order_by('-id')
            [Order.objects.cache_single_order(order) for order in orders_adm]
            if search_query:
                orders_adm = orders_adm.filter(
                    Q(id__icontains=search_query) |
                    Q(status__icontains=search_query) |
                    Q(customer__first_name__icontains=search_query) |
                    Q(customer__last_name__icontains=search_query) |
                    Q(customer__email__icontains=search_query) |
                    Q(customer__username__icontains=search_query)
                )

            # Get the count once and pass it to the custom paginator
            orders_adm_list = list(orders_adm)
            adm_total_count = len(orders_adm_list)
            paginator = Paginator(orders_adm, 10)
            paginator._count = adm_total_count

            # Get the page number from the GET request and get the corresponding page object
            page_number = self.request.GET.get('page')
            page_obj = paginator.get_page(page_number)

            context['orders'] = page_obj
            return context

        orders = list(Order.objects.get_cached_orders(customer=self.request.user).values())

        if search_query:
            orders = [order for order in orders
                      if search_query.lower() in str(order['id']) or search_query.lower() in order['status']]

        total_count = len(orders)
        paginator = Paginator(orders, 10)
        paginator._count = total_count
        page_number = self.request.GET.get('page')
        page_obj = paginator.get_page(page_number)

        context['orders'] = page_obj
        return context


@method_decorator(strict_rate_limit(url_names=['orders:order_detail']), name='dispatch')
class UserOrderDetailView(LoginRequiredMixin, TemplateView):
    template_name = 'orders/order_detail.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user

        # Extract order_id from kwargs
        order_id = kwargs.get('order_id')

        # Fetch the cached order
        order = Order.objects.get_cached_order(order_id=order_id, customer=user)

        # Add order to the context
        context['order'] = order
        return context


@method_decorator(strict_rate_limit(url_names=['orders:create_payment']), name='dispatch')
class PaymentCreateView(LoginRequiredMixin, FormView):
    template_name = 'orders/payment_form.html'
    form_class = PaymentForm
    success_url = reverse_lazy('payments:payment_list')

    def form_valid(self, form):
        user = self.request.user
        order_id = self.kwargs.get('order_id')
        order = Order.objects.select_related('customer').prefetch_related(Prefetch(
            'items',queryset=Item.objects.select_related('product__role_type',
                                                                'product__stock'))
        ).get(id=order_id, customer=user)

        payment_method = form.cleaned_data['payment_method']
        promo_codes = form.cleaned_data['promo_codes']

        try:
            # Call the CreatePayment class to create the payment and get it id.
            payment_service = PaymentService()
            payment_id = payment_service.create_payment(
                user=user,
                order=order,
                payment_type=payment_method,
                promo_codes=promo_codes).id
            payment_service.bulk_create_histories()

            self.kwargs['payment_id'] = payment_id
            messages.success(self.request, "Pagamento criado com sucesso!")

        except ValidationError as e:
            messages.error(self.request, f"Criação do pagamento falhou, motivo: {e}")
            return self.form_invalid(form)

        except Exception:
            messages.error(self.request, "Ocorreu um erro ao criar o pagamento!")

        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['order_id'] = self.kwargs.get('order_id', None)
        return context

    def get_success_url(self):
        payment_id = self.kwargs.pop('payment_id', None)
        if payment_id:
            return reverse('payments:payment_detail', kwargs={'payment_id': payment_id})
        # Se o 'payment_id' não foi definido, retorna para a lista de pagamentos
        return super().get_success_url()

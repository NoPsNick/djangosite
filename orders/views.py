from django.db.models import Q
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
from payments.services import create_payment
from .models import Order
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


@method_decorator(strict_rate_limit(url_names=['orders:order_list']), name='dispatch')
class UserOrderListView(LoginRequiredMixin, TemplateView):
    template_name = 'orders/order_list.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        search_query = self.request.GET.get('search')

        if self.request.user.is_staff:
            orders_adm = Order.objects.all().order_by('-id')
            if search_query:
                orders_adm = orders_adm.filter(
                    Q(id__icontains=search_query) |
                    Q(status__icontains=search_query) |
                    Q(customer__first_name__icontains=search_query) |
                    Q(customer__last_name__icontains=search_query) |
                    Q(customer__email__icontains=search_query) |
                    Q(customer__username__icontains=search_query)
                )

            paginator = Paginator(orders_adm, 10)
            page_number = self.request.GET.get('page')
            page_obj = paginator.get_page(page_number)
            context['orders'] = page_obj
            return context

        orders = Order.objects.get_cached_orders(customer=self.request.user)

        if search_query:
            orders = [order for order in orders
                      if search_query.lower() in str(order['id']) or search_query.lower() in order['status'
                      ] or search_query.lower() in order['customer']]

        paginator = Paginator(orders, 10)
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
    success_url = reverse_lazy('orders:order_list')

    def form_valid(self, form):
        user = self.request.user
        order_id = self.kwargs.get('order_id')  # Get the order ID from the URL
        order = Order.objects.get(id=order_id, customer=user)

        payment_method = form.cleaned_data['payment_method']
        promo_codes = form.cleaned_data['promo_codes']

        try:
            # Call the service function to create the payment
            payment = create_payment(user=user, order=order, payment_method=payment_method, promo_codes=promo_codes)
            messages.success(self.request, "Payment created successfully!")
        except ValidationError as e:
            # Handle any errors that occur during payment creation
            messages.error(self.request, f"Payment failed: {str(e)}")
            return self.form_invalid(form)

        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        # Call the base implementation first to get a context
        context = super().get_context_data(**kwargs)
        # Add your custom context variable
        context['order_id'] = self.kwargs.get('order_id')
        return context

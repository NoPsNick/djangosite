from django.db.models import Q
from django.shortcuts import redirect, get_object_or_404
from django.views import View
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import ValidationError
from django.core.paginator import Paginator
from django.contrib import messages
from django.views.generic import TemplateView

from payments.services import create_payment
from .models import Order
from cart.services import get_cart_items
from orders.services import create_order


class CreateOrderView(LoginRequiredMixin, View):
    def post(self, request, *args, **kwargs):
        # Ensure the user is verified and has an address
        if not request.user.address:
            messages.error(request, "Por favor, adicione um endereço para criar um pedido.")
            return redirect('cart:detail')

        # Get the cart items
        cart_items, total_price = get_cart_items(request)

        if not cart_items:
            messages.error(request, "Seu carrinho está vázio!")
            return redirect('cart:detail')

        # Prepare the items data for the order
        items_data = [{'slug': item['product']['slug'], 'quantity': item['quantity']} for item in cart_items]

        try:
            # Call the create_order function
            create_order(user=request.user, items_data=items_data)
            messages.success(request, "Pedido criado com sucesso!")
            return redirect('orders:order_list')  # Redirect to order list or confirmation page
        except ValidationError as e:
            messages.error(request, str(e))
            return redirect('cart:detail')


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


class CreatePaymentView(LoginRequiredMixin, View):
    def post(self, request, *args, **kwargs):
        # Get the order ID from the URL
        order_id = kwargs.get('order_id')
        payment_method = kwargs.get('payment_method')

        # Fetch the order, ensuring the user is the customer, or the user is staff
        order = get_object_or_404(Order, pk=order_id)
        if not request.user.is_staff and order.customer != request.user:
            messages.error(request, "Um erro ocorreu ao criar o pagamento.")
            return redirect('orders:order_list')

        try:
            # Call the create_payment function
            create_payment(user=request.user, order=order, payment_method=payment_method)
            messages.success(request, "Pagamento criado com sucesso!")
            return redirect('orders:order_list')  # Redirect to orders or payment success page
        except Exception as e:
            messages.error(request, f"Failed to create payment: {str(e)}")
            return redirect('orders:order_list')

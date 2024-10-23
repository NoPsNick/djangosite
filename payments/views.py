from django.db.models import Q
from django.utils.decorators import method_decorator
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.paginator import Paginator
from django.views.generic import TemplateView

from pages.decorators import strict_rate_limit
from .models import Payment


@method_decorator(strict_rate_limit(url_names=['payments:payment_list']), name='dispatch')
class UserPaymentListView(LoginRequiredMixin, TemplateView):
    template_name = 'payments/payment_list.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        search_query = self.request.GET.get('search')

        if self.request.user.is_staff:
            payments_adm = Payment.objects.select_related('payment_method').order_by('-id')
            if search_query:
                payments_adm = payments_adm.filter(
                    Q(id__icontains=search_query) |
                    Q(status__icontains=search_query) |
                    Q(customer__first_name__icontains=search_query) |
                    Q(customer__last_name__icontains=search_query) |
                    Q(customer__email__icontains=search_query) |
                    Q(customer__username__icontains=search_query) |
                    Q(payment_method__name__icontains=search_query) |
                    Q(payment_method__payment_type__icontains=search_query)
                )

            paginator = Paginator(payments_adm, 10)
            page_number = self.request.GET.get('page')
            page_obj = paginator.get_page(page_number)
            context['payments'] = page_obj
            return context

        payments = Payment.objects.get_cached_payments(customer=self.request.user)

        if search_query:
            payments = [payment for payment in payments
                      if search_query.lower() in str(payment['id']) or search_query.lower() in payment['status'
                      ] or search_query.lower() in payment['customer']]

        paginator = Paginator(payments, 10)
        page_number = self.request.GET.get('page')
        page_obj = paginator.get_page(page_number)

        context['payments'] = page_obj
        return context


@method_decorator(strict_rate_limit(url_names=['payments:payment_detail']), name='dispatch')
class UserPaymentDetailView(LoginRequiredMixin, TemplateView):
    template_name = 'payments/payment_detail.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user

        # Extract order_id from kwargs
        payment_id = kwargs.get('payment_id')

        # Fetch the cached order
        payment = Payment.objects.get_cached_payment(payment_id=payment_id, customer=user)

        # Add order to the context
        context['payment'] = payment
        return context

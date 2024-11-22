from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.paginator import Paginator
from django.db.models import Q
from django.views.generic import TemplateView

from .models import UserHistory


class UserHistoryListView(LoginRequiredMixin, TemplateView):
    template_name = 'users/users_history.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        search_query = self.request.GET.get('search')

        if self.request.user.is_staff:
            histories_adm = UserHistory.objects.all().order_by('-id')
            if search_query:
                histories_adm = histories_adm.filter(
                    Q(id__icontains=search_query) |
                    Q(status__icontains=search_query) |
                    Q(user__icontains=search_query)
                )

            histories_adm_list = list(histories_adm)
            adm_total_count = len(histories_adm_list)
            paginator_adm = Paginator(histories_adm, 10)
            paginator_adm._count = adm_total_count

            page_number_adm = self.request.GET.get('page')
            page_obj_adm = paginator_adm.get_page(page_number_adm)
            context['histories'] = page_obj_adm

            return context

        # Precisa utilizar o sorted() por causa que ao adicionar algum novo histórico, ele ficaria no
        # final do dicionário, pois não se pega do banco de dados, e sim utiliza signals.
        histories_dict = UserHistory.objects.get_cached_histories(user_id=self.request.user.id)
        histories = [value for key, value in sorted(histories_dict.items(), reverse=True)]

        if search_query:
            histories = [historic for historic in histories
                      if search_query.lower() in str(historic['id']) or search_query.lower() in historic[
                             'type_display'] or search_query.lower() in historic['info']]

        paginator = Paginator(histories, 10)
        page_number = self.request.GET.get('page')
        page_obj = paginator.get_page(page_number)

        context['histories'] = page_obj
        return context

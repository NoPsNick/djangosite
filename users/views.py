from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.paginator import Paginator
from django.db.models import Q
from django.views.generic import TemplateView

from .models import UserHistory


class UserHistoryListView(LoginRequiredMixin, TemplateView):
    template_name = 'users/users_history.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        search_query = self.request.GET.get('search', '').lower()
        context['histories'] = self.get_histories(search_query)
        return context

    def get_histories(self, search_query):
        if self.request.user.is_staff:
            histories = self.get_staff_histories(search_query)
        else:
            histories = self.get_user_histories(search_query)
        return self.paginate_histories(histories)

    @staticmethod
    def get_staff_histories(search_query):
        histories = UserHistory.objects.select_related('user').order_by('-id')
        if search_query:
            histories = histories.filter(
                Q(id__icontains=search_query) |
                Q(status__icontains=search_query) |
                Q(user__username__icontains=search_query)
            )
        return histories

    def get_user_histories(self, search_query):
        histories_dict = UserHistory.objects.get_cached_histories(user_id=self.request.user.id)
        histories = [value for _, value in sorted(histories_dict.items(), reverse=True)]
        if search_query:
            histories = [
                history for history in histories
                if search_query in str(history['id']) or
                   search_query in history['type_display'].lower() or
                   search_query in history['info'].lower()
            ]
        return histories

    def paginate_histories(self, histories):
        paginator = Paginator(histories, 10)
        paginator._count = len(list(histories))
        page_number = self.request.GET.get('page')
        return paginator.get_page(page_number)

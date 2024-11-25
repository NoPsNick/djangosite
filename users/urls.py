from django.urls import path

from .views import UserHistoryListView

app_name = 'users'

urlpatterns = [
    path('', UserHistoryListView.as_view(), name='historic_list'),
]

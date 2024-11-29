from django.http import Http404
from django.views.generic import TemplateView
from django.core.exceptions import PermissionDenied

from legaldocs.models import TermOfService, PrivacyPolicy, ReturnPolicy
from .services import get_user_data, get_abouts, get_promotions


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

    def get_context_data(self, **kwargs):
        user = self.request.user  # Use the middleware to check the authenticated user
        target_user_id = kwargs.get('user_id', None)  # Extract the target user's id from kwargs
        if not target_user_id:
            raise Http404('Não foi possível encontrar esta página')
        context = super().get_context_data(**kwargs)

        # Ensure the user is authenticated
        if not user.is_authenticated:
            raise PermissionDenied("You must be logged in to view this profile.")
        user_data = get_user_data(user, target_user_id)
        # Allow only the profile owner or staff members to view the profile
        if (user.id != target_user_id and not user.is_staff) or not user_data:
            raise PermissionDenied("You do not have permission to view this profile.")

        # Fetch the profile data using the helper function (from cache or database)
        context['user_data'] = user_data

        return context

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

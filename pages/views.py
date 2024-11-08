from django.views.generic import TemplateView
from django.utils.decorators import method_decorator
from django.core.exceptions import PermissionDenied


from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, viewsets
from rest_framework.throttling import UserRateThrottle
from rest_framework.permissions import IsAuthenticated

from legaldocs.models import TermOfService, PrivacyPolicy, ReturnPolicy
from .decorators import restrict_to_server
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
        target_user_id = kwargs.get('user_id')  # Extract the target user's id from kwargs
        context = super().get_context_data(**kwargs)

        # Ensure the user is authenticated
        if not user.is_authenticated:
            raise PermissionDenied("You must be logged in to view this profile.")

        # Allow only the profile owner or staff members to view the profile
        if user.id != target_user_id and not user.is_staff:
            raise PermissionDenied("You do not have permission to view this profile.")

        # Fetch the profile data using the helper function (from cache or database)
        context['user_data'] = get_user_data(user, target_user_id)

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
class AboutAPIView(APIView):
    throttle_classes = [UserRateThrottle]

    def get(self, request, *args, **kwargs):
        # Tenta obter os dados do cache
        abouts = get_abouts()

        return Response(abouts, status=status.HTTP_200_OK)

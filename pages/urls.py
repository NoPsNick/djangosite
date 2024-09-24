from django.urls import path, include
from django.contrib.auth.decorators import login_required
from rest_framework.routers import DefaultRouter

from .views import (
    AboutAPIView,
    InternalUserViewSet,
    AddressViewSet,
    PhoneNumberViewSet,
    AboutPageView,
    HomePageView,
    ProfilePageView,
    UserAddressAdd,
    UserAddressDelete,
    UserAddressList,
    UserAddressUpdate,
    UserPhoneNumberAdd,
    UserPhoneNumberDelete,
    UserPhoneNumberList,
    UserPhoneNumberUpdate,
    LegalInfos,
)

router = DefaultRouter()
router.register(r'internaluser', InternalUserViewSet, basename='internaluser')
router.register(r'address', AddressViewSet, basename='address')
router.register(r'phone-number', PhoneNumberViewSet, basename='phonenumber')

app_name = "pages"

urlpatterns = [
    path("", HomePageView.as_view(), name="home"),
    path("sobre/", AboutPageView.as_view(), name="about"),
    path("api/about/", AboutAPIView.as_view(), name="about_api"),
    path("perfil/<int:user_id>/", login_required(ProfilePageView.as_view()), name="profile"),

    # User Address URLs
    path("perfil/meusenderecos/", login_required(UserAddressList.as_view()), name="address_list"),
    path("perfil/meusenderecos/adicionar/", login_required(UserAddressAdd.as_view()), name="address_add"),
    path("perfil/meusenderecos/alterar/<int:pk>/", login_required(UserAddressUpdate.as_view()), name="address_update"),
    path("perfil/meusenderecos/remover/<int:pk>/", login_required(UserAddressDelete.as_view()), name="address_delete"),

    # User Phone Number URLs
    path("perfil/meustelefones/", login_required(UserPhoneNumberList.as_view()), name="phone_list"),
    path("perfil/meustelefones/adicionar/", login_required(UserPhoneNumberAdd.as_view()), name="phone_add"),
    path("perfil/meustelefones/alterar/<int:pk>/", login_required(UserPhoneNumberUpdate.as_view()), name="phone_update"),
    path("perfil/meustelefones/remover/<int:pk>/", login_required(UserPhoneNumberDelete.as_view()), name="phone_delete"),

    # API URLs
    path('api/', include(router.urls)),

    # ToS URL
    path('tos/', LegalInfos.as_view(), name='termsofservice'),
]

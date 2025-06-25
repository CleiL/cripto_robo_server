from django.urls import path
from accounts.views.auth_views import RegisterView, LoginView
from accounts.views.profile_views import UserProfileView
from accounts.views.connections_views import BinanceConnectionView

urlpatterns = [
    path('register/', RegisterView.as_view(), name='register'),
    path('login/', LoginView.as_view(), name='login'),
    path('me/', UserProfileView.as_view(), name='user-profile'),
    path('binance/', BinanceConnectionView.as_view(), name='binance-connection'),
]

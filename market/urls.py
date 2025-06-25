from django.urls import path
from market.views import CandleBySymbolView, CandleListView, SymbolListView

urlpatterns = [
    path('candles/', CandleListView.as_view(), name='candle-list'),
    path('symbols/', SymbolListView.as_view(), name='symbol-list'),
    path('candles/<str:symbol>/', CandleBySymbolView.as_view(), name='candles-by-symbol'),
]

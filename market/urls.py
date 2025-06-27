from django.urls import path
from market.views import CandleBySymbolView, CandleListView, CandleWithMovingAveragesView, SymbolListView, UpdateSymbolCandlesView

urlpatterns = [
    path('candles/', CandleListView.as_view(), name='candle-list'),
    path('symbols/', SymbolListView.as_view(), name='symbol-list'),
    path('candles/<str:symbol>/', CandleBySymbolView.as_view(), name='candles-by-symbol'),
    path('update-candles/', UpdateSymbolCandlesView.as_view(), name='update-candles'),
    path('candles/moving-averages/<str:symbol>/<int:medium_fast>/<int:medium_slow>/', CandleWithMovingAveragesView.as_view()),
]

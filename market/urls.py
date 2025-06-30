from django.urls import path
from market.views import CandleAnalysisView, CandleBySymbolView, CandleListView, CandleWithBBView, CandleWithMovingAveragesRSIView, CandleWithMovingAveragesView, SymbolListView, UpdateSymbolCandlesView

urlpatterns = [
    path('candles/', CandleListView.as_view(), name='candle-list'),
    path('symbols/', SymbolListView.as_view(), name='symbol-list'),
    path('candles/<str:symbol>/', CandleBySymbolView.as_view(), name='candles-by-symbol'),
    path('update-candles/', UpdateSymbolCandlesView.as_view(), name='update-candles'),
    path('candles/moving-averages/<str:symbol>/<int:medium_fast>/<int:medium_slow>/', CandleWithMovingAveragesView.as_view()),
    path('candles/moving-averages-rsi/<str:symbol>/<int:medium_fast>/<int:medium_slow>/', CandleWithMovingAveragesRSIView.as_view()),
    path('candles/bollinger/<str:symbol>/<int:medium_fast>/<int:medium_slow>/', CandleWithBBView.as_view()),
    path('analysis/<str:symbol>/<int:medium_fast>/<int:medium_slow>/', CandleAnalysisView.as_view()),
]

from django.shortcuts import render

# Create your views here.
from rest_framework import generics
from rest_framework import status
from market.models import CandleJson
from market.serializers import CandleJsonSerializer
from rest_framework.views import APIView
from rest_framework.response import Response

class CandleListView(generics.ListAPIView):
    queryset = CandleJson.objects.all()
    serializer_class = CandleJsonSerializer

class SymbolListView(APIView):
    def get(self, request):
        symbols = CandleJson.objects.values_list('symbol', flat=True).distinct()
        return Response(sorted(set(symbols)))

class CandleBySymbolView(APIView):
    def get(self, request, symbol):
        candles = CandleJson.objects.filter(symbol=symbol).order_by('timestamp')
        serializer = CandleJsonSerializer(candles, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
from django.shortcuts import render
from rest_framework import generics
from rest_framework import status
from market.models import CandleJson
from market.serializers import CandleJsonSerializer
from rest_framework.views import APIView
from rest_framework.response import Response
from binance.client import Client
from datetime import datetime
import os
import time

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
    
class UpdateSymbolCandlesView(APIView):
    def post(self, request):
        symbol = request.data.get("symbol")
        if not symbol:
            return Response({"detail": "Símbolo não informado"}, status=400)

        api_key = os.getenv("key_binance")
        secret_key = os.getenv("secret_binance")
        client = Client(api_key=api_key, api_secret=secret_key)

        start_date = datetime(2017, 8, 1)
        start_ts = int(start_date.timestamp() * 1000)

        try:
            while True:
                candles = client.get_klines(
                    symbol=symbol,
                    interval='1d',
                    startTime=start_ts,
                    limit=1000
                )

                if not candles:
                    break

                for k in candles:
                    ts = datetime.fromtimestamp(k[0] / 1000).date()
                    dados = {
                        "open": float(k[1]),
                        "high": float(k[2]),
                        "low": float(k[3]),
                        "close": float(k[4]),
                        "volume": float(k[5])
                    }

                    CandleJson.objects.update_or_create(
                        symbol=symbol,
                        timestamp=ts,
                        defaults={"data": dados}
                    )

                start_ts = candles[-1][0] + 1
                time.sleep(0.2)

                if datetime.fromtimestamp(candles[-1][0] / 1000).date() >= datetime.now().date():
                    break

            return Response({"detail": f"Candles atualizados para {symbol}"})

        except Exception as e:
            return Response({"detail": f"Erro: {str(e)}"}, status=500)

class CandleWithMovingAveragesView(APIView):
    def get(self, request, symbol, medium_fast, medium_slow):
        try:
            medium_fast = int(medium_fast)
            medium_slow = int(medium_slow)
        except ValueError:
            return Response({"detail": "Períodos devem ser inteiros"}, status=status.HTTP_400_BAD_REQUEST)

        candles = CandleJson.objects.filter(symbol=symbol).order_by('timestamp')
        serializer = CandleJsonSerializer(candles, many=True)
        data = serializer.data

        if not data:
            return Response({"detail": "No data found for the given symbol"}, status=status.HTTP_404_NOT_FOUND)

        for i in range(len(data)):
            # Fast
            if i >= medium_fast - 1:
                closes = [c['data'].get('close', 0) for c in data[i - medium_fast + 1:i + 1]]
                data[i]['mediumFast'] = round(sum(closes) / medium_fast, 6)
            else:
                data[i]['mediumFast'] = None

            # Slow
            if i >= medium_slow - 1:
                closes = [c['data'].get('close', 0) for c in data[i - medium_slow + 1:i + 1]]
                data[i]['mediumSlow'] = round(sum(closes) / medium_slow, 6)
            else:
                data[i]['mediumSlow'] = None

        return Response(data, status=status.HTTP_200_OK)
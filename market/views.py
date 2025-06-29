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
import statistics

class CandleListView(generics.ListAPIView):
    queryset = CandleJson.objects.all()
    serializer_class = CandleJsonSerializer

class SymbolListView(APIView):
    def get(self, request):
        symbols = CandleJson.objects.values_list('symbol', flat=True).distinct()
        return Response(sorted(set(symbols)))

class CandleBySymbolView(APIView):
    def get(self, request, symbol):
        starr_date = request.query_params.get('start_date')
        end_date = request.query_params.get('end_date')

        if not symbol:
            return Response({"detail": "Símbolo não informado"}, status=400)
        if not starr_date or not end_date:
            return Response({"detail": "Datas não informadas"}, status=400)
        
        try:
            start_date = datetime.strptime(starr_date, '%Y-%m-%d').date()
            end_date = datetime.strptime(end_date, '%Y-%m-%d').date()
        except ValueError:
            return Response({"detail": "Formato de data inválido. Use YYYY-MM-DD"}, status=400)
        
        if start_date > end_date:
            return Response({"detail": "A data de início não pode ser posterior à data de fim"}, status=400)
        if start_date < datetime(2017, 8, 1).date():
            return Response({"detail": "A data de início não pode ser anterior a 01/08/2017"}, status=400)
        if end_date > datetime.now().date():
            return Response({"detail": "A data de fim não pode ser posterior à data atual"}, status=400)
        
        candles = CandleJson.objects.filter(
            symbol=symbol,
            timestamp__range=(start_date, end_date)
        ).order_by('timestamp')
        
        if not candles.exists():
            return Response({"detail": "Nenhum candle encontrado para o símbolo nesse período"}, status=404)
        
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
            return Response(
                {"detail": "Periods must be integers."},
                status=status.HTTP_400_BAD_REQUEST
            )

        start_str = request.query_params.get('start_date')
        end_str = request.query_params.get('end_date')
        start_date = None
        end_date = None

        try:
            if start_str:
                start_date = datetime.strptime(start_str, '%Y-%m-%d').date()
            if end_str:
                end_date = datetime.strptime(end_str, '%Y-%m-%d').date()
        except ValueError:
            return Response(
                {"detail": "Invalid date format. Use YYYY-MM-DD."},
                status=400
            )

        queryset = CandleJson.objects.filter(symbol=symbol)
        if start_date and end_date:
            if start_date > end_date:
                return Response({"detail": "Start date cannot be after end date."}, status=400)
            queryset = queryset.filter(timestamp__range=(start_date, end_date))


        candles = queryset.order_by('timestamp')
        if not candles.exists():
            return Response(
                {"detail": "No candles found for the symbol in this period."},
                status=404
            )

        serializer = CandleJsonSerializer(candles, many=True)
        data = serializer.data

        for i in range(len(data)):
            if i >= medium_fast - 1:
                closes = [c['data'].get('close', 0) for c in data[i - medium_fast + 1:i + 1]]
                data[i]['mediumFast'] = round(sum(closes) / medium_fast, 6)
            else:
                data[i]['mediumFast'] = None

            if i >= medium_slow - 1:
                closes = [c['data'].get('close', 0) for c in data[i - medium_slow + 1:i + 1]]
                data[i]['mediumSlow'] = round(sum(closes) / medium_slow, 6)
            else:
                data[i]['mediumSlow'] = None

        return Response(data, status=status.HTTP_200_OK)

class CandleWithMovingAveragesRSIView(APIView):
    def get(self, request, symbol, medium_fast, medium_slow):
        try:
            medium_fast = int(medium_fast)
            medium_slow = int(medium_slow)
        except ValueError:
            return Response(
                {"detail": "Periods must be integers."},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Get query parameters
        start_str = request.query_params.get('start_date')
        end_str = request.query_params.get('end_date')
        start_date = None
        end_date = None

        try:
            if start_str:
                start_date = datetime.strptime(start_str, '%Y-%m-%d').date()
            if end_str:
                end_date = datetime.strptime(end_str, '%Y-%m-%d').date()
        except ValueError:
            return Response(
                {"detail": "Invalid date format. Use YYYY-MM-DD."},
                status=400
            )

        queryset = CandleJson.objects.filter(symbol=symbol)
        if start_date and end_date:
            if start_date > end_date:
                return Response(
                    {"detail": "Start date cannot be after end date."},
                    status=400
                )
            queryset = queryset.filter(timestamp__range=(start_date, end_date))

        candles = queryset.order_by('timestamp')
        if not candles.exists():
            return Response(
                {"detail": "No candles found for the symbol in this period."},
                status=404
            )

        serializer = CandleJsonSerializer(candles, many=True)
        data = serializer.data

        # Preprocess closes for RSI and MM
        closes = [c['data'].get('close', 0) for c in data]

        for i in range(len(data)):
            # Média Móvel Curta
            if i >= medium_fast - 1:
                data[i]['mediumFast'] = round(sum(closes[i - medium_fast + 1:i + 1]) / medium_fast, 6)
            else:
                data[i]['mediumFast'] = None

            # Média Móvel Longa
            if i >= medium_slow - 1:
                data[i]['mediumSlow'] = round(sum(closes[i - medium_slow + 1:i + 1]) / medium_slow, 6)
            else:
                data[i]['mediumSlow'] = None

            # RSI (fixo em 14 períodos)
            period_rsi = 14
            if i >= period_rsi:
                gains = []
                losses = []
                for j in range(i - period_rsi + 1, i + 1):
                    delta = closes[j] - closes[j - 1]
                    gains.append(delta if delta > 0 else 0)
                    losses.append(-delta if delta < 0 else 0)

                avg_gain = sum(gains) / period_rsi
                avg_loss = sum(losses) / period_rsi

                if avg_loss == 0:
                    rsi = 100
                else:
                    rs = avg_gain / avg_loss
                    rsi = 100 - (100 / (1 + rs))

                data[i]['rsi'] = round(rsi, 2)
            else:
                data[i]['rsi'] = None

        return Response(data, status=status.HTTP_200_OK)

class CandleWithBBView(APIView):
    def get(self, request, symbol, medium_fast, medium_slow):
        # converte parâmetros para inteiro
        try:
            medium_fast = int(medium_fast)
            medium_slow = int(medium_slow)
        except ValueError:
            return Response({"detail": "Periods must be integers."}, status=400)

        # parâmetros de data (query string)
        start_str = request.query_params.get('start_date')
        end_str = request.query_params.get('end_date')

        try:
            start_date = datetime.strptime(start_str, '%Y-%m-%d').date() if start_str else None
            end_date = datetime.strptime(end_str, '%Y-%m-%d').date() if end_str else None
        except ValueError:
            return Response({"detail": "Invalid date format."}, status=400)

        # buscar candles
        queryset = CandleJson.objects.filter(symbol=symbol)
        if start_date and end_date:
            queryset = queryset.filter(timestamp__range=(start_date, end_date))

        candles = queryset.order_by('timestamp')
        if not candles.exists():
            return Response({"detail": "No candles found."}, status=404)

        serializer = CandleJsonSerializer(candles, many=True)
        data = serializer.data

        closes = [c['data']['close'] for c in data]

        for i in range(len(data)):
            # Média móvel curta
            if i >= medium_fast - 1:
                ma_fast = closes[i - medium_fast + 1:i + 1]
                data[i]['mediumFast'] = round(sum(ma_fast) / medium_fast, 6)
            else:
                data[i]['mediumFast'] = None

            # Média móvel longa
            if i >= medium_slow - 1:
                ma_slow = closes[i - medium_slow + 1:i + 1]
                data[i]['mediumSlow'] = round(sum(ma_slow) / medium_slow, 6)
            else:
                data[i]['mediumSlow'] = None

            # RSI padrão 14
            period_rsi = 14
            if i >= period_rsi:
                deltas = [closes[j] - closes[j - 1] for j in range(i - period_rsi + 1, i + 1)]
                gains = [d for d in deltas if d > 0]
                losses = [-d for d in deltas if d < 0]
                avg_gain = sum(gains) / period_rsi
                avg_loss = sum(losses) / period_rsi
                rs = avg_gain / avg_loss if avg_loss != 0 else 0
                rsi = 100 - (100 / (1 + rs)) if avg_loss != 0 else 100
                data[i]['rsi'] = round(rsi, 2)
            else:
                data[i]['rsi'] = None

            # Bollinger Bands (desvio padrão 2)
            if i >= medium_slow - 1:
                close_window = closes[i - medium_slow + 1:i + 1]
                mean = sum(close_window) / medium_slow
                std = (sum([(x - mean) ** 2 for x in close_window]) / medium_slow) ** 0.5
                data[i]['bbUpper'] = round(mean + 2 * std, 6)
                data[i]['bbLower'] = round(mean - 2 * std, 6)
            else:
                data[i]['bbUpper'] = None
                data[i]['bbLower'] = None

        return Response(data, status=200)

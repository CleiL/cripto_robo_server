from django.core.management.base import BaseCommand
from binance.client import Client
from market.models import CandleJson
from datetime import datetime, timedelta
import time
import os

class Command(BaseCommand):
    help = 'Coleta todos os candles da Binance e salva no banco PostgreSQL como JSON'

    def handle(self, *args, **kwargs):
        api_key = os.getenv("key_binance")
        secret_key = os.getenv("secret_binance")

        if not api_key or not secret_key:
            self.stderr.write("❌ API Key ou Secret não encontrados. Verifique o arquivo .env.")
            return

        client = Client(api_key=api_key, api_secret=secret_key)

        # 🔍 Pares com USDT ou BRL
        exchange_info = client.get_exchange_info()
        symbols_info = exchange_info['symbols']
        pares = sorted(set([
            s['symbol'] for s in symbols_info
            if s['status'] == 'TRADING' and s['quoteAsset'] in ['USDT', 'BRL']
        ]))

        # 📅 Data inicial
        start_date = datetime(2017, 8, 1)

        for symbol in pares:
            self.stdout.write(f"⏳ Coletando {symbol}...")
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

                    # Avança para o próximo lote
                    start_ts = candles[-1][0] + 1
                    time.sleep(0.2)

                    # Parar se atingiu o dia atual
                    if datetime.fromtimestamp(candles[-1][0] / 1000).date() >= datetime.now().date():
                        break

                self.stdout.write(self.style.SUCCESS(f"✔ {symbol} finalizado"))
            except Exception as e:
                self.stderr.write(f"❌ Erro com {symbol}: {e}")

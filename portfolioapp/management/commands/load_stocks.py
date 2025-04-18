from django.core.management.base import BaseCommand
from portfolioapp.models import Stock
import yfinance as yf

POPULAR_TICKERS = ['AAPL', 'GOOGL', 'MSFT', 'TSLA', 'AMZN', 'NVDA', 'META', 'NFLX', 'BRK-B', 'JPM']

class Command(BaseCommand):
    help = "Load popular stocks into the database"

    def handle(self, *args, **kwargs):
        for symbol in POPULAR_TICKERS:
            try:
                info = yf.Ticker(symbol).info
                name = info.get("shortName") or info.get("longName") or symbol
                Stock.objects.update_or_create(symbol=symbol, defaults={"name": name})
                self.stdout.write(self.style.SUCCESS(f"Loaded {symbol} - {name}"))
            except Exception as e:
                self.stderr.write(f"Error loading {symbol}: {e}")
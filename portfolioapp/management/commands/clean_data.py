from django.core.management.base import BaseCommand
from portfolioapp import scheduler
from portfolioapp.models import TradeLog, SimulationSession
from datetime import datetime, timedelta
from portfolioapp.libs.tickers import available_tickers

class Command(BaseCommand):
    def _ignore():
        sessions = SimulationSession.objects.all()
        for session in sessions:
            last_trade = TradeLog.objects.filter(session=session).order_by('-timestamp').first()
            print(last_trade.timestamp)
            session.simulated_date = last_trade.timestamp + timedelta(days=1)
            session.save()

    def handle(self, *args, **kwargs):
        for session in SimulationSession.objects.all():
            portfolio = session.portfolio
            for position in portfolio.holdings.all():
                if position.ticker not in available_tickers:
                    portfolio.sell_stock(position.ticker, 
                                         position.shares, 
                                         session=session,
                                         reasoning="Ticker not available",
                                         force=True)

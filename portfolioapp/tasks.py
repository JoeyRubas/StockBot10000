# portfolioapp/tasks.py

from datetime import timedelta
from celery import shared_task
from portfolioapp.models import Portfolio, SimulationSession
from portfolioapp.libs.LLM import start_trade_for_session
from portfolioapp.libs.data_fetchers import stock_data_wrapper


import logging

logging.basicConfig(
    filename="log2.txt", filemode="a", format="%(asctime)s [%(levelname)s] %(message)s", level=logging.ERROR)


def next_market_day(date):
    """Returns the next weekday (skipping Saturday and Sunday)."""
    next_day = date + timedelta(days=1)
    while next_day.weekday() >= 5: 
        next_day += timedelta(days=1)
    return next_day


@shared_task
def log_all_portfolios():
    for session in SimulationSession.objects.all():
        next_day = False
        start_date = session.simulated_date
        while not next_day:
            session.simulated_date = next_market_day(session.simulated_date)
            session.save()
            portfolio = session.portfolio
            try:
                portfolio.log_portfolio_value()
                next_day = True
            except ValueError:
                next_day = False
        print(f"Advanced from {start_date} to {session.simulated_date}")
    for session in SimulationSession.objects.all():
        start_trade_for_session(session.id, "Adjust")


@shared_task
def adjust_portfolios():
    pass

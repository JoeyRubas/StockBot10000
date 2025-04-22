# portfolioapp/tasks.py

from celery import shared_task
from portfolioapp.models import Portfolio, SimulationSession
from portfolioapp.libs.LLM import start_trade_for_session
from portfolioapp.libs.data_fetchers import stock_data_wrapper


@shared_task
def log_all_portfolios():
    for portfolio in Portfolio.objects.all():
        portfolio.log_portfolio_value()


@shared_task
def adjust_portfolios():
    for session in SimulationSession.objects.all():
        start_trade_for_session(session.id, "Adjust")

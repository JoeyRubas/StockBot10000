from celery import shared_task
from portfolioapp.models import SimulationSession
from portfolioapp.libs.LLM import start_trade_for_session

@shared_task
def run_daily_simulations():
    sessions = SimulationSession.objects.all()
    for session in sessions:
        start_trade_for_session(session.id)
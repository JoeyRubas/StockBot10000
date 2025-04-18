from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from django_apscheduler.jobstores import DjangoJobStore
from portfolioapp.models import SimulationSession
from pytz import timezone
import logging

logger = logging.getLogger(__name__)

def daily_trade_job():
    print("📈 Running daily trade job...")
    for session in SimulationSession.objects.all():
        try:
            start_trade(session.id)
            print(f"✅ Trade executed for session {session.id}")
        except Exception as e:
            logger.error(f"Failed to execute trade for session {session.id}: {str(e)}")

def start():
    scheduler = BackgroundScheduler(timezone=timezone("America/New_York"))
    scheduler.add_jobstore(DjangoJobStore(), "default")

    scheduler.add_job(
        daily_trade_job,
        trigger=CronTrigger(hour=9, minute=0),
        id="daily_trade_job",
        name="Run trades for all sessions daily at 9AM ET",
        replace_existing=True,
    )

    scheduler.start()
    print("✅ APScheduler started.")
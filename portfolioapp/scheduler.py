from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from django_apscheduler.jobstores import DjangoJobStore
from portfolioapp.models import SimulationSession
from pytz import timezone
import logging

logger = logging.getLogger(__name__)


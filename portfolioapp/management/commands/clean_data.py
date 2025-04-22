from django.core.management.base import BaseCommand
from portfolioapp import scheduler
from portfolioapp.models import PortfolioLog
from datetime import datetime, timedelta

class Command(BaseCommand):
    
    def handle(self, *args, **kwargs):
        logs = PortfolioLog.objects.all().order_by('portfolio', 'portfolio__session', 'timestamp')
        previous_log = None

        for log in logs:
            if previous_log:
                time_diff = abs(log.timestamp - previous_log.timestamp)
                same_portfolio = log.portfolio == previous_log.portfolio
                same_session = log.portfolio.session == previous_log.portfolio.session

                if time_diff < 120 and (same_portfolio or same_session):
                    previous_log.delete()
            previous_log = log

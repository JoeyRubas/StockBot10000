from django.core.management.base import BaseCommand
from portfolioapp import scheduler

class Command(BaseCommand):
    help = "Starts APScheduler after migrations are applied."

    def handle(self, *args, **kwargs):
        scheduler.start()
        self.stdout.write(self.style.SUCCESS("✅ APScheduler started."))
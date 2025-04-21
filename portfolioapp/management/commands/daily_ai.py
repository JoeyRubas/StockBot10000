from django.core.management.base import BaseCommand
from portfolioapp.tasks import run_daily_simulations


class Command(BaseCommand):
    help = "Run all daily AI simulations for each user session"

    def handle(self, *args, **kwargs):
        run_daily_simulations.delay()
        self.stdout.write(self.style.SUCCESS("Triggered daily AI simulations"))

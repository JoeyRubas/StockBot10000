from django.core.management.base import BaseCommand
from portfolioApp.libs.LLM import start_trade


class Command(BaseCommand):
    help = "Starts the trading process"

    def handle(self, *args, **kwargs):
        start_trade()
        self.stdout.write(self.style.SUCCESS("Trading process started successfully."))

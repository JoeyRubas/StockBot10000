from django.apps import AppConfig


class PortfolioappConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "portfolioapp"

    def ready(self):
        from portfolioapp import scheduler

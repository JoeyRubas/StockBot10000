from django.contrib import admin
from .models import Stock, Portfolio, SimulationSession, Position, PortfolioLog, TradeLog


@admin.register(Stock)
class StockAdmin(admin.ModelAdmin):
    list_display = ("symbol", "name")
    search_fields = ("symbol", "name")


@admin.register(Portfolio)
class PortfolioAdmin(admin.ModelAdmin):
    list_display = ("id", "cash", "created_at")
    readonly_fields = ("created_at",)


@admin.register(SimulationSession)
class SimulationSessionAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "amount", "use_twitter", "use_google", "use_price_history", "created_at")
    list_filter = ("use_twitter", "use_google", "use_price_history")
    search_fields = ("user__username",)
    readonly_fields = ("created_at",)


@admin.register(Position)
class PositionAdmin(admin.ModelAdmin):
    list_display = ("id", "portfolio", "ticker", "shares", "share_price_at_purchase", "purchase_timestamp", "session")
    list_filter = ("ticker",)
    search_fields = ("ticker",)


@admin.register(PortfolioLog)
class PortfolioLogAdmin(admin.ModelAdmin):
    list_display = ("id", "portfolio", "timestamp", "total_value")
    readonly_fields = ("timestamp",)


@admin.register(TradeLog)
class TradeLogAdmin(admin.ModelAdmin):
    list_display = ("id", "session", "action", "symbol", "shares", "total_price", "timestamp")
    list_filter = ("action",)
    search_fields = ("symbol",)
    readonly_fields = ("timestamp",)

from django.db import models
import time
from yfinance import Ticker

class Portfolio(models.Model):
    cash = models.FloatField()

    def buy_stock(self, ticker, shares):
        stock = Ticker(ticker)
        price = stock.info.get("currentPrice")
        if price is None or self.cash < shares * price:
            raise ValueError("Insufficient funds")
        Position.objects.create(
            portfolio=self,
            ticker=ticker.upper(),
            shares=shares,
            share_price=price,
            purchase_timestamp=time.time()
        )
        self.cash -= shares * price
        self.save()

    def sell_stock(self, ticker, shares):
        total = sum(p.shares for p in self.holdings.filter(ticker=ticker))
        if shares > total:
            raise ValueError("Not enough shares")
        price = Ticker(ticker).info.get("currentPrice")
        if price is None:
            raise ValueError("Could not get current price")
        self.cash += shares * price
        for p in self.holdings.filter(ticker=ticker).order_by("purchase_timestamp"):
            if p.shares <= shares:
                shares -= p.shares
                p.delete()
            else:
                p.shares -= shares
                p.save()
                break
        self.save()
        return price * shares
    
    def get_total_value(self):
        value = self.cash
        for pos in self.holdings.all():
            current_price = Ticker(pos.ticker).info.get("currentPrice") or pos.share_price
            value += pos.shares * current_price
        return value
    
    def log_portfolio_value(self):
        PortfolioLog.objects.create(
            portfolio=self,
            total_value=self.get_total_value(),
        )


class Position(models.Model):
    portfolio = models.ForeignKey(Portfolio, on_delete=models.CASCADE, related_name='holdings')
    ticker = models.CharField(max_length=10)
    shares = models.FloatField()
    share_price = models.FloatField()
    purchase_timestamp = models.FloatField(default=time.time)

class PortfolioLog(models.Model):
    portfolio = models.ForeignKey(Portfolio, on_delete=models.CASCADE, related_name='logs')
    timestamp = models.FloatField(default=time.time)
    total_value = models.FloatField()



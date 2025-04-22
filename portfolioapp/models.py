from django.db import models
import time
from portfolioapp.libs.data_fetchers import stock_data_wrapper
from portfolioapp.libs.tickers import available_tickers
from django.contrib.auth.models import User


class Stock(models.Model):
    symbol = models.CharField(max_length=10, unique=True)
    name = models.CharField(max_length=100)

    def __str__(self):
        return f"{self.symbol} - {self.name}"


class Portfolio(models.Model):
    cash = models.FloatField()
    created_at = models.DateTimeField(auto_now_add=True)

    def get_total_value(self):
        value = self.cash
        for pos in self.holdings.all():
            current_price = stock_data_wrapper.get(pos.ticker, "currentPrice")
            value += pos.shares * current_price
        return value

    def log_portfolio_value(self):
        last_log = self.logs.order_by("-timestamp").first()
        value = self.get_total_value()
        if last_log and last_log.total_value == value:
            last_log.timestamp = time.time()
            last_log.save()
            return
        
        PortfolioLog.objects.create(
            portfolio=self,
            total_value=self.get_total_value(),
        )

    def buy_stock(self, ticker, shares, session_id, reasoning="None provided"):
        ticker = ticker.upper()
        price = stock_data_wrapper.get(ticker, "currentPrice")

        if price is None:
            raise ValueError(f"Could not retrieve price for {ticker}")
        if self.cash < shares * price:
            raise ValueError(f"Insufficient funds, available: {self.cash}"
                             f"share price: {price}, shares: {shares}"
                             f"total cost: {shares * price}")

        session = SimulationSession.objects.get(id=session_id)

        Position.objects.create(
            portfolio=self,
            session=session,
            ticker=ticker,
            shares=shares,
            share_price=price,
            purchase_timestamp=time.time(),
        )

        self.cash -= shares * price
        self.save()
        self.log_portfolio_value()

        TradeLog.objects.create(session=session, 
                                action="buy", 
                                symbol=ticker, 
                                shares=shares, 
                                price=price, 
                                reasoning=reasoning)

    def sell_stock(self, ticker, shares, session):

        ticker = ticker.upper()

        if ticker not in available_tickers:
            raise ValueError("Invalid ticker")

        total = sum(p.shares for p in self.holdings.filter(ticker=ticker))
        if shares > total:
            raise ValueError("Not enough shares")


        price = stock_data_wrapper.get(ticker, "currentPrice")

        if price is None:
            raise ValueError(f"Could not retrieve price for {ticker}")

        self.cash += shares * price
        remaining = shares

        for p in self.holdings.filter(ticker=ticker).order_by("purchase_timestamp"):
            if p.shares <= remaining:
                remaining -= p.shares
                p.delete()
            else:
                p.shares -= remaining
                p.save()
                break

        self.save()
        self.log_portfolio_value()

        TradeLog.objects.create(session=session, action="sell", symbol=ticker, shares=shares, price=price)

        return price * shares


class SimulationSession(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    portfolio = models.OneToOneField(Portfolio, on_delete=models.CASCADE, related_name="session")
    amount = models.FloatField()
    use_twitter = models.BooleanField(default=False)
    use_google = models.BooleanField(default=False)
    use_price_history = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    stocks = models.ManyToManyField(Stock, blank=True)
    name = models.CharField(max_length=100, unique=True, default = "Untitled Session")


class Position(models.Model):
    portfolio = models.ForeignKey(Portfolio, on_delete=models.CASCADE, related_name="holdings")
    ticker = models.CharField(max_length=10)
    shares = models.FloatField()
    share_price = models.FloatField()
    purchase_timestamp = models.FloatField(default=time.time)
    session = models.ForeignKey(SimulationSession, on_delete=models.CASCADE, related_name="trades", null=True)


class PortfolioLog(models.Model):
    portfolio = models.ForeignKey(Portfolio, on_delete=models.CASCADE, related_name="logs")
    timestamp = models.FloatField(default=time.time)
    total_value = models.FloatField()


class TradeLog(models.Model):
    session = models.ForeignKey(SimulationSession, on_delete=models.CASCADE, related_name="logs")
    action = models.CharField(max_length=10)  # "buy" or "sell"
    symbol = models.CharField(max_length=10)
    shares = models.FloatField()
    price = models.FloatField()
    timestamp = models.DateTimeField(auto_now_add=True)
    reasoning = models.TextField(null=True, blank=True)

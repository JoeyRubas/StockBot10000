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

    def get_and_update_cash(self):
        cash = self.session.amount
        for trade in self.session.logs.all():
            if trade.action == "buy":
                cash -= trade.total_price
            elif trade.action == "sell":
                cash += trade.total_price
        self.cash = cash
        self.save()
        return cash

    def get_total_value(self):
        
        value = self.get_and_update_cash()

        for pos in self.holdings.all():
            current_price = stock_data_wrapper.get(pos.ticker, self.session.simulated_date)
            value += pos.shares * current_price
        return value

    def log_portfolio_value(self):
        PortfolioLog.objects.create(
            portfolio=self,
            total_value=self.get_total_value(),
            timestamp=self.session.simulated_date.strftime("%Y-%m-%d")
        )

    def buy_stock(self, ticker, shares, session_id, reasoning="None provided"):
        if shares <= 0:
            raise ValueError("Shares must be greater than 0")
        ticker = ticker.upper()
        if ticker not in available_tickers:
            raise ValueError("Invalid ticker")
        
        price = stock_data_wrapper.get(ticker, self.session.simulated_date)

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
            share_price_at_purchase=price,
            purchase_timestamp=session.simulated_date.strftime("%Y-%m-%d"),
        )

        TradeLog.objects.create(session=session, 
                                action="buy", 
                                symbol=ticker, 
                                shares=shares, 
                                total_price=shares * price,
                                share_price=price,
                                profit=0, 
                                reasoning=reasoning,
                                timestamp=session.simulated_date.strftime("%Y-%m-%d"))
        
        self.get_and_update_cash()
        self.save()

    def sell_stock(self, ticker, shares, session, reasoning="None provided", force=False):

        ticker = ticker.upper()
        if ticker not in available_tickers and not force:
            raise ValueError("Invalid ticker")
        
        total = sum(p.shares for p in self.holdings.filter(ticker=ticker))
        if shares > total:
            raise ValueError("Not enough shares")
        try:
            price = stock_data_wrapper.get(ticker, self.session.simulated_date)

        except:
            if not force:
                raise ValueError(f"Could not retrieve price for {ticker}")
            price = self.holdings.filter(ticker=ticker).order_by("-purchase_timestamp").first().share_price_at_purchase
        

        remaining = shares
        profit = 0

        for p in self.holdings.filter(ticker=ticker).order_by("purchase_timestamp"):
            if p.shares <= remaining:
                remaining -= p.shares
                profit += (price - p.share_price_at_purchase) * p.shares
                self.cash += p.shares * price
                p.delete()
            else:
                p.shares -= remaining
                profit += (price - p.share_price_at_purchase) * remaining
                self.cash += remaining * price
                remaining = 0
                self.save()
                p.save()
                break

        self.save()
        

        TradeLog.objects.create(session=session,
                                 action="sell",
                                 symbol=ticker, 
                                 shares=shares, 
                                 total_price=shares * price,
                                 share_price=price,
                                 profit=profit,
                                 reasoning=reasoning,
                                 timestamp=session.simulated_date.strftime("%Y-%m-%d"))

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
    simulated_date = models.DateTimeField(null=True, blank=True)


class Position(models.Model):
    portfolio = models.ForeignKey(Portfolio, on_delete=models.CASCADE, related_name="holdings")
    ticker = models.CharField(max_length=10)
    shares = models.FloatField()
    share_price_at_purchase = models.FloatField()
    purchase_timestamp = models.DateTimeField()
    session = models.ForeignKey(SimulationSession, on_delete=models.CASCADE, related_name="trades", null=True)


class PortfolioLog(models.Model):
    portfolio = models.ForeignKey(Portfolio, on_delete=models.CASCADE, related_name="logs")
    timestamp = models.DateTimeField()
    total_value = models.FloatField()


class TradeLog(models.Model):
    session = models.ForeignKey(SimulationSession, on_delete=models.CASCADE, related_name="logs")
    action = models.CharField(max_length=10)  # "buy" or "sell"
    symbol = models.CharField(max_length=10)
    shares = models.FloatField()
    total_price = models.FloatField()
    share_price = models.FloatField()
    profit = models.FloatField(null=True, blank=True)
    timestamp = models.DateTimeField()
    reasoning = models.TextField(null=True, blank=True)

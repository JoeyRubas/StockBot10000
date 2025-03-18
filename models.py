from sqlalchemy import create_engine, Column, Integer, Float, String, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
import time
import yfinance as yf

Base = declarative_base()

class Position(Base):
    __tablename__ = "positions"

    id = Column(Integer, primary_key=True)
    ticker = Column(String, nullable=False)
    shares = Column(Float, nullable=False)
    share_price = Column(Float, nullable=False)
    purchase_timestamp = Column(Float, default=time.time)
    portfolio_id = Column(Integer, ForeignKey("portfolios.id"))

    def __init__(self, ticker: str, shares: float, share_price: float):
        self.ticker = ticker.upper()
        self.shares = shares
        self.share_price = share_price
        self.purchase_timestamp = time.time()

class Portfolio(Base):
    __tablename__ = "portfolios"

    id = Column(Integer, primary_key=True)
    cash = Column(Float, nullable=False)
    holdings = relationship("Position", backref="portfolio", cascade="all, delete-orphan")

    def __init__(self, cash: float):
        self.cash = cash

    def buy_stock(self, session, ticker: str, shares: float):
        stock = yf.Ticker(ticker)
        share_price = stock.info.get("currentPrice")

        if shares * share_price > self.cash:
            raise ValueError("Insufficient funds to buy the stock.")

        position = Position(ticker, shares, share_price)
        position.portfolio_id = self.id
        self.holdings.append(position)
        self.cash -= shares * share_price

        session.add(position)
        session.commit()

    def sell_stock(self, session, ticker: str, shares: float):
        total_shares = sum(p.shares for p in self.holdings if p.ticker == ticker)
        if total_shares < shares:
            raise ValueError("Not enough shares to sell.")

        stock = yf.Ticker(ticker)
        share_price = stock.info.get("currentPrice")
        profit = shares * share_price
        self.cash += profit

        for position in self.holdings:
            if position.ticker == ticker:
                if position.shares > shares:
                    position.shares -= shares
                    break
                else:
                    shares -= position.shares
                    session.delete(position)
                    if shares == 0:
                        break

        session.commit()
        return profit

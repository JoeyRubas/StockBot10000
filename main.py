from fastapi import FastAPI
from routers import auth, portfolio

app = FastAPI()

app.include_router(auth.router, prefix="/auth", tags=["Auth"])
app.include_router(portfolio.router, prefix="/portfolio", tags=["Portfolio"])


# Optional CLI entrypoint
if __name__ == "__main__":
    from sqlalchemy.orm import Session
    from database import SessionLocal
    from models import Portfolio, Position

    def get_or_create_portfolio(session: Session):
        portfolio = session.query(Portfolio).first()
        if not portfolio:
            print("Creating a new portfolio")
            portfolio = Portfolio(cash=10000)
            session.add(portfolio)
            session.commit()
        return portfolio

    session = SessionLocal()
    portfolio = get_or_create_portfolio(session)
    print(f"Current Cash Balance: ${portfolio.cash:.2f}")

    ticker = "AAPL"
    shares = 5
    existing_position = session.query(Position).filter_by(ticker=ticker).first()
    if not existing_position:
        try:
            print(f"Buying {shares} shares of {ticker}")
            portfolio.buy_stock(session, ticker, shares)
            print("Purchase successful!")
        except ValueError as e:
            print(f"Error: {e}")

    session.close()
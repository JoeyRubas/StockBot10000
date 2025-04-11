from fastapi import APIRouter, UploadFile, File, Depends, HTTPException
import csv
from sqlalchemy.orm import Session
from database import SessionLocal
from models import Portfolio
from auth import verify_token
import requests

router = APIRouter()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.post("/upload")
async def upload_csv(file: UploadFile = File(...), db: Session = Depends(get_db), user=Depends(verify_token)):
    contents = await file.read()
    portfolio = db.query(Portfolio).first()  # For now, single portfolio
    if not portfolio:
        raise HTTPException(status_code=404, detail="Portfolio not found")

    reader = csv.DictReader(contents.decode("utf-8").splitlines())
    for row in reader:
        ticker = row["ticker"]
        shares = float(row["shares"])
        try:
            portfolio.buy_stock(db, ticker, shares)
        except Exception as e:
            raise HTTPException(status_code=400, detail=str(e))
    return {"message": "Portfolio uploaded and processed"}

@router.post("/buy")
def buy(ticker: str, shares: float, db: Session = Depends(get_db), user=Depends(verify_token)):
    portfolio = db.query(Portfolio).first()
    try:
        portfolio.buy_stock(db, ticker, shares)
        return {"message": f"Bought {shares} shares of {ticker}"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/sell")
def sell(ticker: str, shares: float, db: Session = Depends(get_db), user=Depends(verify_token)):
    portfolio = db.query(Portfolio).first()
    try:
        profit = portfolio.sell_stock(db, ticker, shares)
        return {"message": f"Sold {shares} shares of {ticker}", "profit": profit}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/advice")
def get_advice(db: Session = Depends(get_db), user=Depends(verify_token)):
    portfolio = db.query(Portfolio).first()
    holdings = [
        f"{p.shares} shares of {p.ticker} bought at ${p.share_price}"
        for p in portfolio.holdings
    ]
    prompt = "Evaluate this portfolio:\n" + "\n".join(holdings)

    response = requests.post("http://localhost:11434/api/generate", json={
        "model": "llama2",
        "prompt": prompt,
        "stream": False
    })

    if response.ok:
        return {"advice": response.json()["response"]}
    else:
        raise HTTPException(status_code=500, detail="LLM failed to respond")

from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from .models import Portfolio, SimulationSession
from .forms import SessionForm
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404
import json
import os
from portfolioapp.libs.LLM import start_trade_for_session
from django.http import JsonResponse
from .models import PortfolioLog
from .models import Stock
from django.views.decorators.http import require_GET
from django.db.models import Sum
import yfinance as yf
from .models import Portfolio, SimulationSession, Position
from .models import TradeLog
from portfolioapp.libs.LLM import start_trade_for_session
from threading import Thread
import time

LOG_FILE_PATH = "autonomous_trading_log.txt"


@login_required
def session_list(request):
    sessions = SimulationSession.objects.filter(user=request.user).order_by("-created_at")
    return render(request, "session_list.html", {"sessions": sessions})


@login_required
def create_session(request):
    if request.method == "POST":
        form = SessionForm(request.POST)
        if form.is_valid():
            session = form.save(commit=False)
            session.user = request.user
            session.portfolio = Portfolio.objects.create(cash=session.amount)
            session.save()
            form.save_m2m()
            session.portfolio.log_portfolio_value()

            # Start trading in a background thread
            Thread(target=start_trade_for_session, args=(session.id,)).start()

            return redirect("view_session", pk=session.id)
    else:
        form = SessionForm()
    return render(request, "create_session.html", {"form": form})


@login_required
def view_session(request, pk):
    session = get_object_or_404(SimulationSession, pk=pk, user=request.user)
    return render(request, "view_session.html", {"session": session})


@login_required
def delete_session(request, pk):
    session = get_object_or_404(SimulationSession, pk=pk, user=request.user)
    portfolio = session.portfolio
    if portfolio:
        Position.objects.filter(portfolio=portfolio).delete()
        portfolio.delete()
    session.delete()
    return redirect("session_list")


def chat_log_api(request):
    if not os.path.exists(LOG_FILE_PATH):
        return JsonResponse({"messages": []})

    with open(LOG_FILE_PATH, "r") as file:
        lines = file.readlines()

    return JsonResponse({"messages": lines[-100:]})


def get_portfolio():
    return Portfolio.objects.first()


@csrf_exempt
def buy(request):
    data = json.loads(request.body)
    ticker = data["ticker"]
    shares = float(data["shares"])
    p = get_portfolio()
    try:
        p.buy_stock(ticker, shares)
        return JsonResponse({"message": f"Bought {shares} shares of {ticker}"})
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=400)


@csrf_exempt
def sell(request):
    data = json.loads(request.body)
    ticker = data["ticker"]
    shares = float(data["shares"])
    p = get_portfolio()
    try:
        profit = p.sell_stock(ticker, shares)
        return JsonResponse({"message": f"Sold {shares} shares of {ticker}", "profit": profit})
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=400)


@login_required
def portfolio_value_data(request, pk):
    logs = PortfolioLog.objects.filter(portfolio__session__id=pk).order_by("timestamp")
    data = [{"x": log.timestamp, "y": round(log.total_value)} for log in logs]
    return JsonResponse(data, safe=False)


@require_GET
def stock_search_api(request):
    query = request.GET.get("q", "").upper()
    results = []
    if query:
        try:
            stock = yf.Ticker(query)
            info = stock.info
            if "shortName" in info:
                results.append({"symbol": query, "name": info["shortName"]})
        except Exception:
            pass
    return JsonResponse(results, safe=False)


def search_stocks(request):
    query = request.GET.get("q", "").strip().upper()
    if not query:
        return JsonResponse([], safe=False)

    # Example: filter to top matches from major stocks
    tickers_to_try = [query + suffix for suffix in ["", ".NS", ".AX", ".TO", ".L"]]
    results = []

    for ticker in tickers_to_try:
        try:
            stock = yf.Ticker(ticker)
            info = stock.info
            name = info.get("shortName") or info.get("longName")
            if name:
                results.append({"symbol": ticker, "name": name})
        except Exception:
            continue

        if len(results) >= 5:
            break

    return JsonResponse(results, safe=False)


def search_stocks(request):
    query = request.GET.get("q", "").upper()
    matches = [
        {"symbol": "AAPL", "name": "Apple Inc."},
        {"symbol": "MSFT", "name": "Microsoft Corp"},
        {"symbol": "GOOGL", "name": "Alphabet Inc."},
    ]
    filtered = [m for m in matches if query in m["symbol"]]
    return JsonResponse(filtered, safe=False)


@login_required
def get_holdings(request, pk):
    session = get_object_or_404(SimulationSession, pk=pk, user=request.user)
    holdings = session.portfolio.holdings.values("ticker", "share_price").annotate(total=Sum("shares"))
    data = [{"ticker": h["ticker"], "shares": h["total"], "value": h["total"] * h["share_price"]} for h in holdings]
    data.append({"ticker": "Cash", "shares": "N/A", "value": session.portfolio.cash})
    return JsonResponse(data, safe=False)

@login_required
def get_trades(request, pk):
    session = get_object_or_404(SimulationSession, pk=pk, user=request.user)
    trades = TradeLog.objects.filter(session=session).order_by("timestamp")
    data = [{
        "timestamp": trade.timestamp.strftime("%Y-%m-%d %H:%M:%S"),
        "action": trade.action,
        "symbol": trade.symbol,
        "shares": trade.shares,
        "price": trade.price,
        "reasoning": trade.reasoning,
    } for trade in trades]



    return JsonResponse(data, safe=False)

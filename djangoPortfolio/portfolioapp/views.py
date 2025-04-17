from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from .models import Portfolio
import json
from portfolioapp.libs.LLM import start_trade
from django.shortcuts import render
import os

LOG_FILE_PATH = "autonomous_trading_log.txt"


def chat_view(request):
    start_trade()
    return render(request, "chat_feed.html")


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

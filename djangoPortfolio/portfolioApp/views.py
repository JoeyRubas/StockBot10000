from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from .models import Portfolio
import json
import requests

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

def advice(request):
    p = get_portfolio()
    lines = [
        f"{h.shares} shares of {h.ticker} bought at ${h.share_price}"
        for h in p.holdings.all()
    ]
    prompt = "Evaluate this portfolio:\n" + "\n".join(lines)

    response = requests.post("http://localhost:11434/api/generate", json={
        "model": "llama2",
        "prompt": prompt,
        "stream": False
    })

    if response.ok:
        return JsonResponse({"advice": response.json()["response"]})
    return JsonResponse({"error": "LLM failed to respond"}, status=500)

from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from .models import Portfolio, SimulationSession
from .forms import SessionForm
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404
import json
import os
from portfolioapp.libs.LLM import start_trade
from django.http import JsonResponse
from .models import PortfolioLog

LOG_FILE_PATH = "autonomous_trading_log.txt"


@login_required
def session_list(request):
    sessions = SimulationSession.objects.filter(user=request.user).order_by('-created_at')
    return render(request, 'session_list.html', {'sessions': sessions})


@login_required
def create_session(request):
    if request.method == 'POST':
        form = SessionForm(request.POST)
        if form.is_valid():
            session = form.save(commit=False)
            session.user = request.user
            session.save()
            return redirect('view_session', pk=session.id)
    else:
        form = SessionForm()
    return render(request, 'create_session.html', {'form': form})


@login_required
def view_session(request, pk):
    session = get_object_or_404(SimulationSession, pk=pk, user=request.user)
    return render(request, "view_session.html", {"session": session})


@login_required
def delete_session(request, pk):
    session = get_object_or_404(SimulationSession, pk=pk, user=request.user)
    session.delete()
    return redirect("session_list")


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

@login_required
def portfolio_value_data(request, pk):
    logs = PortfolioLog.objects.filter(portfolio__session__id=pk).order_by("timestamp")
    data = [
        {"x": log.timestamp, "y": log.total_value}
        for log in logs
    ]
    return JsonResponse(data, safe=False)
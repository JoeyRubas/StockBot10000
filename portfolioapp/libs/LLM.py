import asyncio
import os
import time
from dotenv import load_dotenv
from typing import Dict, Union
from django.db.models import Sum
from autogen_core.tools import FunctionTool
from autogen_core.models import ModelFamily
from autogen_agentchat.agents import AssistantAgent
from autogen_agentchat.conditions import TextMentionTermination
from autogen_agentchat.teams import MagenticOneGroupChat
from autogen_agentchat.ui import Console
from autogen_agentchat.messages import TextMessage
from autogen_ext.models.openai import OpenAIChatCompletionClient

from portfolioapp.models import Portfolio, SimulationSession
from portfolioapp.libs.data_fetchers import DataFetcher

# === Setup ===
load_dotenv()
fetcher = DataFetcher(
    type="url",
    url="https://news.google.com/rss/search?q={topic}&hl=en-US&gl=US&ceid=US:en"
)

custom_model_client = OpenAIChatCompletionClient(
    model="openai/gpt-3.5-turbo",
    base_url="https://openrouter.ai/api/v1",
    api_key=os.getenv("OPENROUTER_API_KEY"),
    model_info={
        "vision": False,
        "function_calling": True,
        "json_output": True,
        "structured_output": False,
        "family": ModelFamily.UNKNOWN,
    },
)

# === Tool Implementations ===

def get_active_portfolio():
    return Portfolio.objects.first()

def buy(symbol: str, amount: float) -> str:
    print(f"[DEBUG] Attempting to buy {amount} of {symbol}")
    portfolio = get_active_portfolio()
    try:
        result = portfolio.buy_stock(symbol, amount)
        print("[DEBUG] Buy successful.")
        return f"Successfully bought {amount} shares of {symbol}."
    except Exception as e:
        print("[DEBUG] Buy failed:", e)
        return f"Buy failed: {str(e)}"

def sell(symbol: str, amount: float) -> str:
    """Sell a stock."""
    portfolio = get_active_portfolio()
    try:
        total_value = portfolio.sell_stock(symbol, amount)
        return f"Successfully sold {amount} shares of {symbol} for ${total_value:.2f}."
    except Exception as e:
        return f"Sell failed: {str(e)}"

def get_portfolio() -> Dict[str, float]:
    """Get portfolio holdings."""
    portfolio = get_active_portfolio()
    holdings = portfolio.holdings.values("ticker").annotate(total=Sum("shares"))
    return {entry["ticker"]: entry["total"] for entry in holdings}

def get_data() -> Dict[str, Union[str, float]]:
    """Fetch stock market news."""
    news = fetcher.fetch("STOCK MARKET NEWS")
    return {"news": news}

# === Tool Wrapping ===

tools = [
    FunctionTool(buy, name="buy", description="Buy a stock."),
    FunctionTool(sell, name="sell", description="Sell a stock."),
    FunctionTool(get_data, name="get_data", description="Fetch news."),
    FunctionTool(get_portfolio, name="get_portfolio", description="Check portfolio."),
]

# === Agent Creation ===

def create_agent(name, description, system_message, tools=None):
    # Extract the actual function references if tools are FunctionTool instances
    return AssistantAgent(
    name=name,
    model_client=custom_model_client,
    description=description,
    system_message=system_message,
    tools=tools or []
)

# === Group Chat Runner ===

async def run_stockbot_group_chat(agent_configs, task):
    interfacing_agent = create_agent(
        name="interfacing_agent",
        description="Handles trades and market info.",
        system_message = (
            "You are an autonomous trading agent for a simulated portfolio. "
            "Your primary responsibility is to analyze market data and stock news, "
            "and take trading actions to grow the portfolio. You must use the available tools "
            "to BUY or SELL stocks when you detect opportunities. "
            "If market sentiment is positive, consider buying the related stock. "
            "If sentiment is negative or risk is high, consider selling. "
            "Do not wait for others to tell you when to act — make proactive decisions "
            "that benefit the portfolio. Monitor the portfolio regularly and optimize for growth."
        ),
        tools=tools
    )

    agents = [interfacing_agent]
    for config in agent_configs:
        agents.append(
            create_agent(
                name=config["name"],
                description=config["description"],
                system_message=config["system_message"]
            )
        )

    termination = TextMentionTermination("TERMINATE")
    group_chat = MagenticOneGroupChat(
        agents,
        termination_condition=termination,
        model_client=custom_model_client
    )

    await Console(group_chat.run_stream(task=task))

# === Entry Point ===

def start_trade_for_session(session_id):
    session = SimulationSession.objects.get(id=session_id)
    Portfolio.objects.all().delete()
    portfolio = Portfolio.objects.create(cash=session.amount)
    session.portfolio = portfolio
    session.save()

    time.sleep(1)

    agent_configs = []

    task = (
    "You are a trading agent. "
    "You must buy 1 share of GOOG immediately. "
    "Do not wait. Do not analyze. Just call the buy function."
)

    asyncio.run(run_stockbot_group_chat(agent_configs, task))
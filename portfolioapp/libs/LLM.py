import asyncio
import os
import time
import logging
from dotenv import load_dotenv
from typing import Dict, Union
from django.db.models import Sum
from autogen_core.tools import FunctionTool
from autogen_core.models import ModelFamily
from autogen_agentchat.agents import AssistantAgent
from autogen_agentchat.conditions import TextMentionTermination
from autogen_agentchat.teams import MagenticOneGroupChat
from autogen_agentchat.ui import Console
from autogen_ext.models.openai import OpenAIChatCompletionClient

from portfolioapp.models import Portfolio, SimulationSession
from portfolioapp.libs.data_fetchers import DataFetcher

# === Setup Logging ===
logging.basicConfig(
    filename='log.txt',
    filemode='a',
    format='%(asctime)s [%(levelname)s] %(message)s',
    level=logging.DEBUG
)

# === Load Environment ===
load_dotenv()

# === Custom Client ===
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

# === Shared Tool Store ===
tool_context = {
    "session_id": None,
}

# === Tool Implementations ===
def get_active_portfolio():
    portfolio = Portfolio.objects.filter(session__id=tool_context["session_id"]).first()
    logging.debug(f"Fetched portfolio: {portfolio}")
    return portfolio

def buy(symbol: str, amount: float) -> str:
    logging.debug(f"Attempting to buy {amount} of {symbol}")
    portfolio = get_active_portfolio()
    if not portfolio:
        logging.error("Buy failed: No active portfolio found.")
        return "No active portfolio found."
    try:
        result = portfolio.buy_stock(symbol, amount, session_id=tool_context["session_id"])
        logging.debug(f"Buy result: {result}")
        return f"Successfully bought {amount} shares of {symbol}."
    except Exception as e:
        logging.error(f"Buy failed: {e}")
        return f"Buy failed: {str(e)}"

def sell(symbol: str, amount: float) -> str:
    portfolio = get_active_portfolio()
    if not portfolio:
        return "No active portfolio found."
    try:
        session = SimulationSession.objects.get(id=tool_context["session_id"])
        result = portfolio.sell_stock(symbol, amount, session=session)
        logging.debug(f"Sell result: {result}")
        return f"Successfully sold {amount} shares of {symbol}."
    except Exception as e:
        logging.error(f"Sell failed: {e}")
        return f"Sell failed: {str(e)}"

def get_portfolio() -> Dict[str, float]:
    portfolio = get_active_portfolio()
    if not portfolio:
        return {"error": "No active portfolio found."}
    holdings = portfolio.holdings.values("ticker").annotate(total=Sum("shares"))
    logging.debug(f"Current portfolio holdings: {holdings}")
    return {entry["ticker"]: entry["total"] for entry in holdings}

def get_data() -> Dict[str, Union[str, float]]:
    try:
        session = SimulationSession.objects.get(id=tool_context["session_id"])
        data = {}

        if session.use_twitter:
            twitter_fetcher = DataFetcher(type="twitter")
            data["twitter"] = twitter_fetcher.fetch_twitter_data()

        if session.use_google:
            google_fetcher = DataFetcher(type="google")
            data["google"] = google_fetcher.fetch_google_trends()

        if session.use_price:
            price_fetcher = DataFetcher(type="price")
            data["price"] = price_fetcher.fetch_price_history()

        return data or {"message": "No data sources enabled for this session."}

    except Exception as e:
        logging.error(f"Data fetch failed: {e}")
        return {"error": str(e)}

# === Tool Wrapping ===
tools = [
    FunctionTool(buy, name="buy", description="Buy a stock. Params: symbol, amount"),
    FunctionTool(sell, name="sell", description="Sell a stock."),
    FunctionTool(get_data, name="get_data", description="Fetch data from enabled sources (twitter, google, price)."),
    FunctionTool(get_portfolio, name="get_portfolio", description="Check portfolio."),
]

# === Agent Creator ===
def create_agent(name, description, system_message, tools=None):
    return AssistantAgent(
        name=name,
        model_client=custom_model_client,
        description=description,
        system_message=system_message,
        tools=tools or []
    )

# === Async Group Chat Runner ===
async def run_stockbot_group_chat(agent_configs, task):
    interfacing_agent = create_agent(
        name="interfacing_agent",
        description="Handles trades and market info.",
        system_message=(
            "You are an autonomous trading agent managing a simulated portfolio. "
            "You may use all available cash to buy stocks. "
            "Use the tools available (get_data, buy, sell, get_portfolio). "
            "If the user specifies which stocks are allowed, ONLY use those. "
            "If not, you can use any publicly traded stocks. "
            "Make decisions using Twitter, Google Trends, and Price History data, if enabled."
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

    async for event in group_chat.run_stream(task=task):
        logging.info(f"GroupChat Event: {event}")
        if hasattr(event, "function_call"):
            logging.info(f"Function called: {event.function_call.name}")

# === Entry Point for External Call ===
def start_trade_for_session(session_id):
    logging.info(f"Starting trade session for ID: {session_id}")
    session = SimulationSession.objects.get(id=session_id)
    if session.portfolio:
        session.portfolio.delete()

    portfolio = Portfolio.objects.create(cash=session.amount)
    session.portfolio = portfolio
    session.save()

    # Inject session_id into tool context
    tool_context["session_id"] = session.id

    agent_configs = []

    task = (
        "Execute a trading strategy based on available data sources. "
        "Spend the full portfolio amount to buy stocks. "
        "If user-specified stocks exist, only trade those. "
        "Use available tools and data sources to guide decisions. "
        "Trade can include both buying and selling. End by calling TERMINATE."
    )

    asyncio.run(run_stockbot_group_chat(agent_configs, task))
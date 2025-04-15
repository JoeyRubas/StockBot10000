import asyncio
import datetime
from autogen_core.models import ModelFamily
from autogen_agentchat.agents import AssistantAgent
from autogen_agentchat.conditions import TextMentionTermination
from autogen_agentchat.teams import MagenticOneGroupChat
from autogen_agentchat.ui import Console
from autogen_ext.models.openai import OpenAIChatCompletionClient
from portfolioApp.models import Portfolio 
from django.db.models import Sum
from typing import Dict, Union
from .data_fetchers import fetch_google_news, fetch_market_data, fetch_twitter_sentiment
from .schema import stock_functions

custom_model_client = OpenAIChatCompletionClient(
    model="ollama/llama3.2:latest",
    base_url="http://0.0.0.0:4000",
    api_key="NotRequired",
    model_info={
        "vision": False,
        "function_calling": True,
        "json_output": True,
        "family": ModelFamily.UNKNOWN
    },
)


def get_active_portfolio():
    return Portfolio.objects.first()  

def buy(symbol: str, amount: float) -> str:
    portfolio = get_active_portfolio()
    try:
        portfolio.buy_stock(symbol, amount)
        return f"Successfully bought {amount} shares of {symbol}."
    except Exception as e:
        return f"Buy failed: {str(e)}"

def sell(symbol: str, amount: float) -> str:
    portfolio = get_active_portfolio()
    try:
        total_value: float = portfolio.sell_stock(symbol, amount)
        return f"Successfully sold {amount} shares of {symbol} for ${total_value:.2f}."
    except Exception as e:
        return f"Sell failed: {str(e)}"

def get_portfolio() -> Dict[str, float]:
    portfolio = get_active_portfolio()
    holdings = portfolio.holdings.values('ticker').annotate(total=Sum('shares'))
    return {entry['ticker']: entry['total'] for entry in holdings}

""" def get_data(source: str, symbol: str) -> Dict[str, Union[str, float]]:
    if source == "market":
        return fetch_market_data(symbol)
    elif source == "headlines":
        return fetch_google_news(symbol)
    elif source == "twitter":
        return fetch_twitter_sentiment(symbol)
    return {"error": "Invalid source"} """

def get_data() -> Dict[str, Union[str, float]]:
    return fetch_google_news()


class FileLoggerRunner:
    def __init__(self, group_chat, log_path="chat_log.txt"):
        self.group_chat = group_chat
        self.log_path = log_path
        with open(self.log_path, "a") as f:
            f.write(f"\n\n===== New Chat Started: {datetime.datetime.now()} =====\n")

    async def run_stream(self, task):
        async for message in self.group_chat.run_stream(task=task):
            sender, text = message.get("name"), message.get("content")
            log_entry = f"{sender}: {text}\n"
            with open(self.log_path, "a") as f:
                f.write(log_entry)
    
def create_agent(name, description, system_message):
    return AssistantAgent(
        name=name,
        model_client=custom_model_client,
        description=description,
        system_message=system_message,
    )

def build_tools(schema_list, function_implementations):
    tools = []
    for func_schema in schema_list:
        name = func_schema["name"]
        if name not in function_implementations:
            raise ValueError(f"Missing implementation for function '{name}'")
        tools.append({
            "name": name,
            "description": func_schema.get("description", ""),
            "parameters": func_schema.get("parameters", {"type": "object", "properties": {}}),
            "function": function_implementations[name],
        })
    return tools


async def run_stockbot_group_chat(agent_configs, task):
    agents = [create_agent(**config) for config in agent_configs]
    trading_agent = AssistantAgent(
        name="interfacing_agent",
        model_client=custom_model_client,
        description="Handles data fetching and trades using the Portfolio model.",
        system_message="You're the interface to the stock trading system. " \
                      "Call functions to fetch data, get the current portfolio, " \
                      "and execute trades on behalf of the user.",
        tools=[buy, sell, get_data, get_portfolio]
    )

    agents.insert(0, trading_agent)
    termination = TextMentionTermination("TERMINATE")
    group_chat = MagenticOneGroupChat(agents, termination_condition=termination, model_client=custom_model_client)
    await Console(group_chat.run_stream(task=task))

def start_trade():
    Portfolio.objects.all().delete()
    Portfolio.objects.create(cash=10000)  # Initialize with $10,000
    agent_configs = [
        {
            "name": "upside_searcher",
            "description": "Plans financial strategies looking for the biggest upside opportunities.",
            "system_message": "You are a financial strategist. Identify stocks with the highest potential for growth and suggest trades.",
        },
        {
            "name": "risk_assessment_agent",
            "description": "Assesses risk and suggests mitigations.",
            "system_message": "You assess portfolio risk and suggest diversification or hedging tactics to minimize potential losses.",
        },
    ]
    task = (
        "You are part of a simulated stock trade experiment, where you trade in a fake"
        "portfolio, based on real stocks and data. One agent in the group chat, "
        "the interfacing agent, will manage and access real data about the news and market, while the other agents "
        "are tasked with analyzing the data and making decisions. Note that the interfacing agenct"
        "is your only legitmate source of outside data, and the other agents do not have access outside of their own knowledge"
        "Work together to decide what trades to make based "
        "on the data, and try to maximize the simulated portfolio's value."
        "You can only buy and sell publicly traded stocks, no bonds, crypto, ETFs, or other assets." 
        "Your portfolio will begin with $10,000 cash, and no holdings."
        "The interfacing agent will begin your discussion by fetching recent headlines."
    )
    asyncio.run(run_stockbot_group_chat(agent_configs, task))
    
import asyncio
import datetime
from autogen_agentchat.agents import AssistantAgent
from autogen_agentchat.conditions import TextMentionTermination
from autogen_agentchat.teams import RoundRobinGroupChat
from autogen_agentchat.ui.base import UI
from autogen_ext.models.openai import OpenAIChatCompletionClient
from portfolioApp.models import Portfolio 
from django.db.models import Sum
from libs.data_fetchers import fetch_google_news, fetch_market_data, fetch_twitter_sentiment
from libs.schema import stock_functions

custom_model_client = OpenAIChatCompletionClient(
    model="ollama/llama3.2:latest",
    base_url="http://0.0.0.0:4000",
    api_key="NotRequired",
    model_info={
        "vision": False,
        "function_calling": True,
        "json_output": True,
    },
)


def get_active_portfolio():
    return Portfolio.objects.first()  

def buy(symbol, amount):
    portfolio = get_active_portfolio()
    try:
        portfolio.buy_stock(symbol, amount)
        return f"Successfully bought {amount} shares of {symbol}."
    except Exception as e:
        return f"Buy failed: {str(e)}"

def sell(symbol, amount):
    portfolio = get_active_portfolio()
    try:
        total_value = portfolio.sell_stock(symbol, amount)
        return f"Successfully sold {amount} shares of {symbol} for ${total_value:.2f}."
    except Exception as e:
        return f"Sell failed: {str(e)}"

def get_portfolio():
    portfolio = get_active_portfolio()
    holdings = portfolio.holdings.values('ticker').annotate(total=Sum('shares'))
    return {entry['ticker']: entry['total'] for entry in holdings}

def get_data(source, symbol):
    if source == "market":
        return fetch_market_data(symbol)
    elif source == "headlines":
        return fetch_google_news(symbol)
    elif source == "twitter":
        return fetch_twitter_sentiment(symbol)
    return {"error": "Invalid source"}



class FileLoggerUI(UI):
    def __init__(self, log_path="chat_log.txt"):
        self.log_path = log_path
        with open(self.log_path, "a") as f:
            f.write(f"\n\n===== New Chat Started: {datetime.datetime.now()} =====\n")

    async def display_message(self, sender_name: str, message: str):
        log_entry = f"{sender_name}: {message}\n"
        with open(self.log_path, "a") as f:
            f.write(log_entry)

def create_agent(name, description, system_message):
    return AssistantAgent(
        name=name,
        model_client=custom_model_client,
        description=description,
        system_message=system_message,
    )

async def run_stockbot_group_chat(agent_configs, task, log_file="chat_log.txt"):
    agents = [create_agent(**config) for config in agent_configs]
    trading_agent = AssistantAgent(
        "interfacing_agent",
        model_client=custom_model_client,
        description="Handles data fetching and trades using the Portfolio model.",
        system_message="You're the interface to the stock trading system. "
                       "Call functions to fetch stock data, get the current portfolio, "
                       "and execute trades on behalf of the user.",
        functions=stock_functions,
        function_map={
            "buy": buy,
            "sell": sell,
            "get_data": get_data,
            "fetch_current_portfolio": get_portfolio,
        },
    )
    agents.append(trading_agent)
    termination = TextMentionTermination("TERMINATE")
    group_chat = RoundRobinGroupChat(agents, termination_condition=termination)
    logger_ui = FileLoggerUI(log_path=log_file)
    await logger_ui.run_stream(group_chat.run_stream(task=task))

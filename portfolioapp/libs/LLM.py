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
from datetime import timedelta

from portfolioapp.models import Portfolio, SimulationSession
from portfolioapp.libs.data_fetchers import google_news_fetcher, twitter_news_fetcher, stock_data_wrapper
from portfolioapp.libs.tickers import available_tickers

load_dotenv()

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

prompts = {
        "Start": "Execute a trading strategy based on available data sources. "
        "Spend the full portfolio amount to buy stocks. "
        "If user-specified stocks exist, only trade those. "
        "Use available tools and data sources to guide decisions. "
        "Trade can include both buying and selling. End by calling TERMINATE."
        "The simulation is being called for the first time, so the portfolio is empty. "
        "and only cash is available. "
        "Please use all of the cash to purchase your initial stocks."
        "Please be sure to diversify, and buy at least 3 different stocks."
        "Write unique 1-2 sentence reasoning for each stock you buy or sell ",
        
        "Adjust": "Execute a trading strategy based on available data sources. "
        "Spend the full portfolio amount to buy stocks. "
        "If user-specified stocks exist, only trade those. "
        "Use available tools and data sources to guide decisions. "
        "Trade can include both buying and selling. End by calling TERMINATE."
        "The simulation began earlier, so the portfolio may contain stocks. "
        "Please first check the portfolio to see if there are any stocks. "
        "Then proceed to update your positions by buying or selling stocks. "
        "Please be sure to diversify, and buy at least 3 different stocks. "
        "Updates shoulld not be static, make at least 3 trades, for at least 30 percent of the portfolio. "
        "Write unique 1-2 sentence reasoning for each stock you buy or sell ",
    }


class LLMSession:
    def __init__(self, session_id):
        self.session_id = session_id
        self.session = SimulationSession.objects.get(id=session_id)
        self.portfolio = self.session.portfolio
    


    def buy(self, symbol: str, amount: float, reasoning : str) -> str:
        logging.debug(f"Attempting to buy {amount} of {symbol}")
        portfolio = self.portfolio
        if not portfolio:
            logging.error("Buy failed: No active portfolio found.")
            return "No active portfolio found."
        try:
            result = portfolio.buy_stock(symbol, amount, session_id=self.session_id, reasoning=reasoning)
            logging.debug(f"Buy result: {result}")
            return f"Successfully bought {amount} shares of {symbol}."
        except Exception as e:
            logging.error(f"Buy failed: {e}")
            return f"Buy failed: {str(e)}"


    def sell(self, symbol: str, amount: float, reasoning : str) -> str:
        portfolio = self.portfolio
        if not portfolio:
            return "No active portfolio found."
        try:
            session = SimulationSession.objects.get(id=self.session_id)
            result = portfolio.sell_stock(symbol, amount, session=session, reasoning=reasoning)
            logging.debug(f"Sell result: {result}")
            return f"Successfully sold {amount} shares of {symbol}."
        except Exception as e:
            logging.error(f"Sell failed: {e}")
            return f"Sell failed: {str(e)}"


    def get_portfolio(self) -> Dict[str, float]:
        portfolio = self.portfolio
        if not portfolio:
            return {"error": "No active portfolio found."}
        holdings = portfolio.holdings.all()
        logging.debug(f"Current portfolio holdings: {holdings}")
        return [{"ticker": h.ticker, 
                 "shares": h.shares,
                 "co": h.share_price_at_purchase,
                 "current_share_price" : stock_data_wrapper.get(h.ticker, self.session.simulated_date)} 
                                                                for h in holdings]


    def get_data(self) -> Dict[str, Union[str, float]]:
        try:
            data = {}

            date = self.session.simulated_date

            if self.session.use_twitter:
                data["twitter"] = twitter_news_fetcher.fetch("STOCK MARKET NEWS",
                                                             date = date)
                for ticker in available_tickers:
                    data[f"{ticker}_twitter"] = google_news_fetcher.fetch(ticker, 
                                                                                date=date,
                                                                                count=2)


            if self.session.use_google:
                data["google"] = google_news_fetcher.fetch("STOCK MARKET NEWS",
                                                           date=date)
                for ticker in available_tickers:
                    data[f"{ticker}_google"] = google_news_fetcher.fetch(ticker, 
                                                                                     date=date,
                                                                                     count=2)

            if self.session.use_price_history:
                for ticker in available_tickers:
                    data[f"{ticker}_yesterday"] = stock_data_wrapper.get(ticker, date - timedelta(days=1))
                    data[ticker] = google_news_fetcher.fetch_market_data(ticker, date=date)

            return data or {"message": "No data sources enabled for this session. You are to proceed without data."}

        except Exception as e:
            logging.error(f"Data fetch failed: {e}")
            return {"error": str(e)}


    def create_agent(self, name, description, system_message, tools=None):
        return AssistantAgent(
            name=name,
            model_client=custom_model_client,
            description=description,
            system_message=system_message,
            tools=tools or [],
        )


    async def run_stockbot_group_chat(self, task):
        tools = [
            FunctionTool(self.buy, name="buy", description="Buy a stock."),
            FunctionTool(self.sell, name="sell", description="Sell a stock."),
        ]
        interfacing_agent = self.create_agent(
            name="interfacing_agent",
            description="Handles trades and market info.",
            system_message=(
                "You are an autonomous trading agent managing a simulated portfolio. "
                "You may use all available cash to buy stocks. "
                "Use the tools available (buy, sell). "
                "Make decisions using Twitter, Google Trends, and Price History data, if enabled."
            ),
            tools=tools,
        )

        analyst_agent = self.create_agent(
            name="analyst_agent",
            description="Handles decision making and analysis.",
            system_message=(
                "You are an autonomous trading agent managing a simulated portfolio. "
                "You may use all available cash to buy stocks. "
                "You are specifically responsible for making decisions based on the data provided. "
                "You will be provided with data from Twitter, Google Trends, and Price History. "
                "You will also be provided with the current portfolio. "
            )
        )

        agents = [interfacing_agent, analyst_agent]

        termination = TextMentionTermination("TERMINATE")
        group_chat = MagenticOneGroupChat(agents, termination_condition=termination, model_client=custom_model_client)

        async for event in group_chat.run_stream(task=task):
            logging.info(f"GroupChat Event: {event}")
            if hasattr(event, "function_call"):
                logging.info(f"Function called: {event.function_call.name}")


   


def start_trade_for_session(session_id, stage="Start"):
    logging.info(f"Starting trade session for ID: {session_id}")
    session = SimulationSession.objects.get(id=session_id)
    
    if not session.portfolio:
        portfolio = Portfolio.objects.create(cash=session.amount)
        session.portfolio = portfolio
        session.save()

    llm_session = LLMSession(session_id)


    task = prompts[stage]
    current_portfolio = str(llm_session.get_portfolio())
    data = str(llm_session.get_data())
    full_input = f"{task} Current portfolio: {current_portfolio}. Data: {data}"

    asyncio.run(llm_session.run_stockbot_group_chat(full_input))

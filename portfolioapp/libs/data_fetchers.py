import json
import os
import time
import feedparser
import yfinance as yf
from portfolioapp.libs.tickers import available_tickers
from fuzzywuzzy import process
from datetime import datetime, timedelta
import random
from dotenv import load_dotenv
import pandas as pd

load_dotenv()
use_logged_data = False
topics = ["STOCK MARKET NEWS", "POLITICS NEWS", "ECONOMICS NEWS", "TECH NEWS", "BUSINESS NEWS"] + available_tickers


import yfinance as yf
from datetime import datetime
from portfolioapp.libs.tickers import available_tickers

class StockDataWrapper:
    def __init__(self):
        self.cached_data = {}
        today_str = datetime.now().strftime("%Y-%m-%d")
        for ticker in available_tickers:
            self.cached_data[ticker] = {}
            df = yf.download(ticker, start='2024-01-01', end=today_str)
            for index, row in df.iterrows():
                date_str = index.strftime("%Y-%m-%d")
                self.cached_data[ticker][date_str] = float(row['Close'].iloc[0])

    def get(self, ticker, date):
        if ticker not in available_tickers:
            raise ValueError(f"Invalid ticker: {ticker}")

        date_str = date.strftime("%Y-%m-%d")
        if date_str not in self.cached_data.get(ticker, {}):
            raise ValueError(f"No data available for {ticker} on {date_str}")

        return self.cached_data[ticker][date_str]



stock_data_wrapper = StockDataWrapper()


google_url = "https://news.google.com/rss/search?q={topic}&hl=en-US&gl=US&ceid=US:en"
twitter_url = "https://news.google.com/rss/search?q=%24{topic}+site:twitter.com&hl=en-US&gl=US&ceid=US:en"


class DataFetcher:
    def __init__(self, type, url=None, folder=None, info=""):
        """
        For url, include {topic} in the URL where the topic should be inserted.

        """
        self.type = type
        if type == "url":
            assert url is not None, "URL must be provided for type 'url'"
            self.url = url
      
        self.info = info

    def fetch(self, query, date: datetime = None, count=5):
        query = query.upper()
        if query not in topics:
            if "MARKET_DATA" in query:
                ticker_part = query.replace("MARKET_DATA_", "")
                if ticker_part not in available_tickers:
                    raise ValueError(f"Invalid ticker: {ticker_part}")
            elif query in available_tickers:
                query = f"STOCK MARKET {query}"
            else:
                match = process.extractOne(query, topics)
                if match[1] < 70:
                    raise ValueError(f"No matching topic found for '{query}'")
                query = match[0]

        query = query.replace(" ", "+")

        if date:
            start_str = date.strftime("%Y-%m-%d")
            end_str = (date + timedelta(days=1)).strftime("%Y-%m-%d")
            query += f"+after:{start_str}+before:{end_str}"

        if self.type == "url":
            formatted_url = self.url.format(topic=query)
            data = feedparser.parse(formatted_url).entries
            result = [entry.title for entry in data]
            result = result[:count]
            return ' '.join(result)


    def fetch_market_data(self, ticker, date):
        return {
            "currentPrice": stock_data_wrapper.get(ticker, date),
        }


# Singleton instance for Google News
google_news_fetcher = DataFetcher(type="url", url=google_url)
# Singleton instance for Twitter News
twitter_news_fetcher = DataFetcher(type="url", url=twitter_url)
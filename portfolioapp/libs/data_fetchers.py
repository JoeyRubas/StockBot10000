import json
import feedparser
from yfinance import Ticker
from portfolioapp.libs.tickers import available_tickers
from fuzzywuzzy import process
from datetime import datetime


use_logged_data = False
topics = ["STOCK MARKET NEWS", "POLITICS NEWS", "ECONOMICS NEWS", "TECH NEWS", "BUSINESS NEWS"] + available_tickers


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
        elif type == "folder":
            assert folder is not None, "Folder must be provided for type 'folder'"
            self.folder = folder
        else:
            raise ValueError("Invalid type. Must be 'url' or 'folder'.")
        self.info = info

    def fetch(self, query):
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

        if self.type == "url":
            formatted_url = self.url.format(topic=query)
            data = feedparser.parse(formatted_url).entries
            result = [entry.title for entry in data]
            result = result[:5]
            return f"Result for {query}: {' '.join(result)}"

        elif self.type == "folder":
            now = datetime.now()
            minutes = (now.minute // 10) * 10
            filename = f"{self.folder}/{now.hour:02d}-{minutes:02d}.json"
            with open(filename, "r") as file:
                raw_data = json.load(file)
            return raw_data.get(query, [])

    def fetch_market_data(self, ticker="APPL"):
        if self.type == "folder":
            return self.fetch(f"MARKET_DATA_{ticker}")

        stock = Ticker(ticker)
        info = stock.info
        return {
            "currentPrice": info.get("currentPrice"),
            "previousClose": info.get("previousClose"),
            "marketCap": info.get("marketCap"),
            "volume": info.get("volume"),
            "dayHigh": info.get("dayHigh"),
            "dayLow": info.get("dayLow"),
        }


# Singleton instance for Google News
google_news_fetcher = DataFetcher(type="url", url=google_url)
# Singleton instance for Twitter News
twitter_news_fetcher = DataFetcher(type="url", url=twitter_url)


def fetch_google_news():
    try:
        return {"news": google_news_fetcher.fetch("STOCK MARKET NEWS")}
    except Exception as e:
        return {"error": str(e)}

import feedparser
from yfinance import Ticker


def fetch_google_news(topic="stock market"):
    topic = topic.replace(" ", "+")
    feed_url = f"https://news.google.com/rss/search?q={topic}&hl=en-US&gl=US&ceid=US:en"
    feed = feedparser.parse(feed_url)
    return [{
        'title': entry.title,
        'summary': entry.get('summary', ''),
        'link': entry.link,
        'published': entry.published
    } for entry in feed.entries]


def fetch_twitter_sentiment(ticker="APPL"):
    query = f"%24{ticker}+site:twitter.com"
    feed_url = f"https://news.google.com/rss/search?q={query}&hl=en-US&gl=US&ceid=US:en"
    feed = feedparser.parse(feed_url)
    return [{
        'title': entry.title,
        'link': entry.link,
        'published': entry.published
    } for entry in feed.entries]


def fetch_market_data(ticker="APPL"):
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

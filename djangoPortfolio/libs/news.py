import feedparser

def fetch_google_news(topic="stock market"):
    topic = topic.replace(" ", "+")
    feed_url = f"https://news.google.com/rss/search?q={topic}&hl=en-US&gl=US&ceid=US:en"
    feed = feedparser.parse(feed_url)
    return [{
        'title': entry.title,
        'summary': entry.summary,
        'link': entry.link,
        'published': entry.published
    } for entry in feed.entries]

news = fetch_google_news()
for item in news:
    print(item["title"])

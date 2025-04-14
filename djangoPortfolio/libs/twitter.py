import feedparser

def fetch_twitter_rss_via_google(ticker="TSLA"):
    query = f"%24{ticker}+site:twitter.com"
    feed_url = f"https://news.google.com/rss/search?q={query}&hl=en-US&gl=US&ceid=US:en"
    feed = feedparser.parse(feed_url)
    return [{
        'title': entry.title,
        'link': entry.link,
        'published': entry.published
    } for entry in feed.entries]

tweets = fetch_twitter_rss_via_google("TSLA")
for t in tweets:
    print(t["title"])

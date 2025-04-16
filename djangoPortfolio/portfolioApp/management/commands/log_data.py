import os
import json
import time
from datetime import datetime, timedelta

from django.core.management.base import BaseCommand
from portfolioApp.libs.tickers import available_tickers
from portfolioApp.libs.data_fetchers import DataFetcher, google_url, twitter_url


class Command(BaseCommand):
    help = "Fetch and log stock/news data every 10 minutes for 24 hours"

    def add_arguments(self, parser):
        parser.add_argument(
            "--folder",
            type=str,
            default="daily_data",
            help="Folder to save fetched data"
        )

    def handle(self, *args, **options):
        folder = options["folder"]
        os.makedirs(folder, exist_ok=True)

        google_fetcher = DataFetcher(type="url", url=google_url)
        twitter_fetcher = DataFetcher(type="url", url=twitter_url)

        ticker_topics = [f"STOCK MARKET {ticker}" for ticker in available_tickers]
        topics = ["STOCK MARKET NEWS", "POLITICS NEWS", "ECONOMICS NEWS", "TECH NEWS", "BUSINESS NEWS"] + ticker_topics

        
        start_time = datetime.now()
        end_time = start_time.replace(hour=17, minute=0, second=0, microsecond=0)
        if datetime.now() >= end_time:
            end_time += timedelta(days=1)

        while datetime.now() < end_time:
            now = datetime.now()
            minutes = (now.minute // 10) * 10
            timestamp = f"{now.hour:02d}-{minutes:02d}"
            data = {}

            for topic in topics:
                try:
                    google_results = google_fetcher.fetch(topic)
                    twitter_results = twitter_fetcher.fetch(topic)
                    data[topic.upper()] = {
                        "google": google_results,
                        "twitter": twitter_results
                    }
                except Exception as e:
                    data[topic.upper()] = {"error": str(e)}

            for ticker in available_tickers:
                try:
                    data[f"MARKET_DATA_{ticker}"] = google_fetcher.fetch_market_data(ticker)
                except Exception as e:
                    data[f"MARKET_DATA_{ticker}"] = {"error": str(e)}

            filepath = os.path.join(folder, f"{timestamp}.json")
            with open(filepath, "w") as f:
                json.dump(data, f, indent=2)

            self.stdout.write(f"[{now.strftime('%H:%M')}] Logged data to {filepath}")

            sleep_seconds = 600 - (datetime.now().timestamp() % 600)
            time.sleep(sleep_seconds)

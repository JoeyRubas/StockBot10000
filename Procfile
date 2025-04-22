web: gunicorn djangoPortfolio.wsgi:application
worker: celery -A djangoPortfolio worker --loglevel=info
beat: celery -A djangoPortfolio beat --loglevel=info
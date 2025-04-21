web: gunicorn stockbot10000.wsgi:application
worker: celery -A stockbot10000 worker --loglevel=info
beat: celery -A stockbot10000 beat --loglevel=info
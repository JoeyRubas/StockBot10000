To run:

```
pyenv install 3.11
pipenv install
pipenv shell
```

celery -A djangoPortfolio worker --beat --loglevel=info
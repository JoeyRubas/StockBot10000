from django.urls import path
from . import views

urlpatterns = [
    path("buy/", views.buy),
    path("sell/", views.sell),
    path("advice/", views.advice),
]

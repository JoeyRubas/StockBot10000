from django.urls import path
from . import views

urlpatterns = [
    path("buy/", views.buy),
    path("sell/", views.sell),
    path("chat/", views.chat_view, name="chat_view"),
    path("api/chat-log/", views.chat_log_api, name="chat_log_api"),

]

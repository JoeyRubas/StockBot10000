from django.urls import path
from . import views

urlpatterns = [
    path("buy/", views.buy),
    path("sell/", views.sell),
    path("chat/", views.chat_view, name="chat_view"),
    path("api/chat-log/", views.chat_log_api, name="chat_log_api"),
    path("", views.session_list, name="session_list"),
    path("session/create/", views.create_session, name="create_session"),
    path("session/<int:pk>/", views.view_session, name="view_session"),
    path("session/<int:pk>/delete/", views.delete_session, name="delete_session"),
    path('session/<int:pk>/value-data/', views.portfolio_value_data, name='portfolio_value_data'),
]
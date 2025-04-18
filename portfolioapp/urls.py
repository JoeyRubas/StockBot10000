from django.urls import path
from . import views
from .views import search_stocks

urlpatterns = [
    path("buy/", views.buy),
    path("sell/", views.sell),
    path("api/chat-log/", views.chat_log_api, name="chat_log_api"),
    path("", views.session_list, name="session_list"),
    path("session/create/", views.create_session, name="create_session"),
    path("session/<int:pk>/", views.view_session, name="view_session"),
    path("session/<int:pk>/delete/", views.delete_session, name="delete_session"),
    path('session/<int:pk>/value-data/', views.portfolio_value_data, name='portfolio_value_data'),
    path("api/search-stocks/", views.stock_search_api, name="stock_search_api"),
    path("api/search-stocks/", search_stocks, name="search_stocks"),
    path("api/search-stocks/", views.search_stocks, name="search_stocks"),
    path("session/<int:pk>/holdings/", views.get_holdings, name="get_holdings"),
]
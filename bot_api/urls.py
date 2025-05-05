from django.urls import path
from .views import *
from .views import OrderDetailView  # Import the appropriate view

urlpatterns = [
    path('auth/', BotAuthView.as_view(), name='bot-auth'),

    path('orders/all/', ManagerOrderListView.as_view(), name='manager-orders'),
    path('orders/my/', ClientOrderListView.as_view(), name='client-orders'),

    path('user/me/', CurrentUserView.as_view(), name='current-user'),

    path('orders/<int:order_id>/', OrderDetailView.as_view(), name='order-detail'),  # New view for single order
    path('orders/<int:order_id>/status/', OrderStatusUpdateView.as_view(), name='update-order-status'),
]

from rest_framework import serializers
from django.contrib.auth import get_user_model
from AdversGroup.models import Order  # Импортируем модели из основного приложения

User = get_user_model()

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'is_staff']

class OrderSerializer(serializers.ModelSerializer):
    class Meta:
        model = Order
        fields = ['id', 'order_number', 'status', 'created_at']
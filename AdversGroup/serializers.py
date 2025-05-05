from rest_framework import serializers
from AdversGroup.models import Order


class OrderSerializer(serializers.ModelSerializer):
    status_display = serializers.CharField(source='get_status_display', read_only=True)

    class Meta:
        model = Order
        fields = [
            'id',
            'order_number',
            'status',
            'status_display',
            'created_at',
            'total_amount',
            'user'
        ]
        extra_kwargs = {
            'user': {'read_only': True}
        }
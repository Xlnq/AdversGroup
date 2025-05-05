from django.http import JsonResponse
from rest_framework.generics import ListAPIView
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.authentication import TokenAuthentication
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework import status, generics
from django.contrib.auth import authenticate
from AdversGroup.models import Order
import logging
from AdversGroup.serializers import OrderSerializer
from rest_framework.authtoken.models import Token

from djangoProject.views import logger

# Константы статусов заказов
ORDER_STATUSES = {
    'created': 'Создан',
    'processing': 'В обработке',
    'completed': 'Завершен',
    'cancelled': 'Отменен'
}


class ManagerOrderListView(generics.ListAPIView):
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if user.is_superuser:
            return Order.objects.all()
        return Order.objects.filter(user=user)

    serializer_class = OrderSerializer


class ClientOrderListView(generics.ListAPIView):
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Order.objects.filter(user=self.request.user)

    serializer_class = OrderSerializer


class BotAuthView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        username = request.data.get('username')
        password = request.data.get('password')

        user = authenticate(username=username, password=password)
        if not user:
            return Response({'detail': 'Invalid credentials'}, status=400)

        Token.objects.filter(user=user).delete()
        token = Token.objects.create(user=user)

        return Response({
            'token': token.key,
            'user_id': user.pk,
            'is_staff': user.is_staff,
            'is_superuser': user.is_superuser
        })


class CurrentUserView(APIView):
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        logging.debug(f"Authenticated user: {user}")
        return Response({
            'id': user.id,
            'username': user.username,
            'email': user.email,
            'is_staff': user.is_staff,
        })


class OrderStatusUpdateView(APIView):
    permission_classes = [IsAuthenticated]

    def patch(self, request, order_id):
        try:
            order = Order.objects.get(id=order_id)
            user = request.user

            # Проверка прав
            if not user.is_staff and order.user != user:
                return JsonResponse(
                    {'detail': 'У вас нет прав для изменения этого заказа.'},
                    status=status.HTTP_403_FORBIDDEN
                )

            new_status = request.data.get('status')

            # Валидация статуса
            if new_status not in ORDER_STATUSES:
                return JsonResponse(
                    {'detail': 'Неверный статус. Допустимые значения: ' + ', '.join(ORDER_STATUSES.keys())},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # Логирование изменения статуса
            old_status = order.status
            order.status = new_status
            order.save()

            logger.info(
                f"Статус заказа #{order_id} изменен с {old_status} на {new_status} "
                f"пользователем {user.username} (ID: {user.id})"
            )

            return JsonResponse({
                'detail': f'Статус заказа успешно изменен.',
                'order_id': order_id,
                'old_status': old_status,
                'new_status': new_status
            })

        except Order.DoesNotExist:
            return JsonResponse(
                {'detail': 'Заказ не найден.'},
                status=status.HTTP_404_NOT_FOUND
            )


class OrderListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        if user.is_staff:
            orders = Order.objects.all()
        else:
            orders = Order.objects.filter(user=user)

        serializer = OrderSerializer(orders, many=True)
        return Response(serializer.data)


class OrderDetailView(APIView):
    permission_classes = [IsAuthenticated]  # Ensure that only authenticated users can access this

    def get(self, request, order_id):
        try:
            # Retrieve the order by its ID
            order = Order.objects.get(id=order_id)

            # Check if the user is allowed to view this order
            if order.user != request.user and not request.user.is_staff:
                return Response({'detail': 'You do not have permission to view this order.'},
                                status=status.HTTP_403_FORBIDDEN)

            # Serialize the order data
            serializer = OrderSerializer(order)
            return Response(serializer.data)

        except Order.DoesNotExist:
            return Response({'detail': 'Order not found.'}, status=status.HTTP_404_NOT_FOUND)
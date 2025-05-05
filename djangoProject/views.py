from rest_framework.permissions import IsAuthenticated
from AdversGroup.models import Order
from .serializers import OrderSerializer
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.contrib.auth import authenticate
from rest_framework.authtoken.models import Token
from django.contrib.auth import get_user_model
import logging

logger = logging.getLogger(__name__)

User = get_user_model()


class BotAuthView(APIView):
    def post(self, request, *args, **kwargs):
        logger.info(f"Incoming auth request: {request.data}")

        username = request.data.get('username')
        password = request.data.get('password')

        if not username or not password:
            logger.warning("Missing credentials")
            return Response(
                {"detail": "Требуется username и password"},
                status=status.HTTP_400_BAD_REQUEST
            )

        logger.info(f"Attempting auth for: {username}")

        # Используем email для аутентификации
        user = authenticate(request, username=username, password=password)

        if not user:
            logger.warning(f"Invalid credentials for: {username}")
            return Response(
                {"detail": "Неверные учетные данные"},
                status=status.HTTP_401_UNAUTHORIZED
            )

        try:
            token, created = Token.objects.get_or_create(user=user)
            logger.info(f"Auth successful for user: {user.id}")

            return Response({
                "token": token.key,
                "user_id": user.id,
                "email": user.email,
                "is_staff": user.is_staff
            })

        except Exception as e:
            logger.error(f"Token error: {str(e)}", exc_info=True)
            return Response(
                {"detail": "Ошибка сервера при создании токена"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

class OrderListAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        orders = Order.objects.filter(user=request.user)
        serializer = OrderSerializer(orders, many=True)
        return Response(serializer.data)

class OrderDetailAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        order = Order.objects.get(pk=pk, user=request.user)
        serializer = OrderSerializer(order)
        return Response(serializer.data)

    def patch(self, request, pk):
        order = Order.objects.get(pk=pk, user=request.user)
        serializer = OrderSerializer(order, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=400)


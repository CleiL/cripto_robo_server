from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from accounts.models import BinanceAccount
from accounts.serializers import BinanceAccountSerializer


class BinanceConnectionView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        binance, _ = BinanceAccount.objects.get_or_create(user=request.user)
        serializer = BinanceAccountSerializer(binance)
        return Response(serializer.data)


    def put(self, request):
        binance, _ = BinanceAccount.objects.get_or_create(user=request.user)
        serializer = BinanceAccountSerializer(binance, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save(user=request.user)
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

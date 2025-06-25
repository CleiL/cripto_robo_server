from rest_framework import serializers
from market.models import CandleJson

class CandleJsonSerializer(serializers.ModelSerializer):
    class Meta:
        model = CandleJson
        fields = ['id', 'symbol', 'timestamp', 'data']

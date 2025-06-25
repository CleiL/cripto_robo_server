from rest_framework import serializers
from django.contrib.auth import authenticate
from rest_framework.validators import UniqueValidator
from rest_framework import serializers
from accounts.models import BinanceAccount, CustomUser

class RegisterSerializer(serializers.ModelSerializer):
    email = serializers.EmailField(
        required=True,
        validators=[
            UniqueValidator(queryset=CustomUser.objects.all(), message="This email is already registered.")
        ]
    )
    password = serializers.CharField(write_only=True, required=True, min_length=8)
    phone = serializers.CharField(required=False, allow_blank=True, max_length=15)
    username = serializers.CharField(required=False, allow_blank=True, max_length=50)
    full_name = serializers.CharField(required=False, allow_blank=True, max_length=150)

    class Meta:
        model = CustomUser
        fields = ('email', 'password', 'phone', 'username', 'full_name')

    def create(self, validated_data):
        email = validated_data['email']
        username = email.split('@')[0]
        user = CustomUser.objects.create_user(
            email=validated_data['email'],
            username=username,
            password=validated_data['password'],
            phone=validated_data.get('phone', ''),
            full_name=validated_data.get('full_name', '')
        )
        return user

class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField(required=True)
    password = serializers.CharField(write_only=True, required=True, min_length=8)

    def validate(self, attrs):
        email = attrs.get('email')
        password = attrs.get('password')

        try:
            user = CustomUser.objects.get(email=email)
        except CustomUser.DoesNotExist:
            raise serializers.ValidationError("Email ou senha inválidos")

        if not user.check_password(password):
            raise serializers.ValidationError("Email ou senha inválidos")

        attrs['user'] = user
        return attrs


class UserProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomUser
        fields = ['id', 'email', 'username', 'full_name', 'phone', 'password']
        extra_kwargs = {
            'password': {'write_only': True, 'required': False}
        }

    def to_representation(self, instance):
        data = super().to_representation(instance)

        # Máscara para email
        email = data.get('email')
        if email and '@' in email:
            user_part, domain_part = email.split('@')
            half = len(user_part) // 2
            data['email'] = user_part[:half] + '*' * (len(user_part) - half) + '@' + domain_part

        # Máscara para senha
        data['password'] = '***********'

        return data

    def update(self, instance, validated_data):
        if 'password' in validated_data:
            instance.set_password(validated_data.pop('password'))
        return super().update(instance, validated_data)

class BinanceAccountSerializer(serializers.ModelSerializer):
    class Meta:
        model = BinanceAccount
        fields = ['id', 'api_key', 'api_secret', 'created_at', 'updated_at']
        extra_kwargs = {
            'api_secret': {'write_only': True},
            'api_key': {'write_only': True},
        }

    def to_representation(self, instance):
        data = super().to_representation(instance)

        # Se quiser mostrar mascarado no GET (em vez de ocultar)
        data['api_key'] = '************'
        data['api_secret'] = '************'

        return data

    def update(self, instance, validated_data):
        instance.api_key = validated_data.get('api_key', instance.api_key)
        instance.api_secret = validated_data.get('api_secret', instance.api_secret)
        instance.save()
        return instance

    def create(self, validated_data):
        user = self.context['request'].user
        return BinanceAccount.objects.create(user=user, **validated_data)



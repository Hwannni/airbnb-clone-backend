from rest_framework import serializers
from .models import Category


class CategorySerializer(serializers.ModelSerializer):

    # Category 모델의 정보를 가져와 serializer 해줌
    class Meta:
        model = Category
        # 모든 필드를 허용
        fields = "__all__"

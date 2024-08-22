from rest_framework.serializers import ModelSerializer
from .models import User


class TinyUserSerializer(ModelSerializer):
    class Meta:
        model = User
        # 보여주고 싶은 user 정보만 필드에 담기
        fields = (
            "name",
            "avatar",
            "username",
        )

from rest_framework.serializers import ModelSerializer
from .models import Amenity, Room
from users.serializers import TinyUserSerializer
from categories.serializers import CategorySerializer


class AmenitySerializer(ModelSerializer):
    class Meta:
        model = Amenity
        fields = (
            "name",
            "description",
        )


class RoomDatailSerializer(ModelSerializer):

    # user의 serializer 가져오기
    # owner 정보는 사용자가 마음대로 수정하면 안된다.
    owner = TinyUserSerializer(read_only=True)
    amenities = AmenitySerializer(many=True)
    category = CategorySerializer()

    class Meta:
        model = Room
        fields = "__all__"


class RoomListSerializer(ModelSerializer):
    class Meta:
        model = Room
        fields = (
            "pk",
            "name",
            "country",
            "city",
            "price",
        )
        # ID대신 object로 확장
        depth = 1

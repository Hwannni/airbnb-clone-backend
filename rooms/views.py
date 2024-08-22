from rest_framework.views import APIView
from rest_framework.status import HTTP_204_NO_CONTENT
from rest_framework.response import Response
from rest_framework.exceptions import NotFound, NotAuthenticated
from .models import Amenity, Room
from .serializers import AmenitySerializer, RoomListSerializer, RoomDatailSerializer


class Amenities(APIView):

    def get(self, request):
        all_amenities = Amenity.objects.all()
        serializer = AmenitySerializer(
            all_amenities,
            many=True,
        )
        return Response(serializer.data)

    def post(self, request):
        serializer = AmenitySerializer(data=request.data)
        if serializer.is_valid():
            amenity = serializer.save()
            return Response(
                AmenitySerializer(amenity).data,
            )
        else:
            return Response(serializer.errors)


class AmenityDetail(APIView):

    # 각 pk가 존재하는지 try-except 문을 통해 검증
    def get_object(self, pk):
        try:
            return Amenity.objects.get(pk=pk)
        except Amenity.DoesNotExist:
            raise NotFound

    def get(self, request, pk):
        # 1. pk가 가지고 있는 amenity를 담고
        amenity = self.get_object(pk)
        # 2. amenity를 serializer화 하고
        serializer = AmenitySerializer(amenity)
        # 3. serializer.data를 response 한다.
        return Response(serializer.data)

    def put(self, request, pk):
        amenity = self.get_object(pk)
        # put 메소드의 경우 DB의 amenity와 사용자가 보낸 amenity
        # 모두 가져와야 하기 때문에 인자가 2개 필요하다.
        # partial=True --> 부분적 업데이트 가능
        serializer = AmenitySerializer(
            amenity,
            data=request.data,
            partial=True,
        )
        # 업데이트 하려는 내용을 검증
        if serializer.is_valid():
            # 업데이트 내용을 저장
            updated_amenity = serializer.save()
            # 저장된 데이터를 serializer화
            # response로 return
            return Response(
                AmenitySerializer(updated_amenity).data,
            )
        else:
            return Response(serializer.errors)

    def delete(self, request, pk):
        amenity = self.get_object(pk)
        amenity.delete()
        return Response(status=HTTP_204_NO_CONTENT)


class Rooms(APIView):

    def get(self, request):
        all_rooms = Room.objects.all()
        serializer = RoomListSerializer(all_rooms, many=True)
        return Response(serializer.data)

    def post(self, request):
        if request.user.is_authenticated:
            serializer = RoomDatailSerializer(data=request.data)
            if serializer.is_valid():
                # serializer에게 owner가 user라는 것을 알려준다.
                # owner 데이터는 필수이기 때문에 반드시 이 작업을 해야한다.
                room = serializer.save(owner=request.user)
                serializer = RoomDatailSerializer(room)
                return Response(serializer.data)
            else:
                return Response(serializer.errors)
        else:
            raise NotAuthenticated


class RoomDetail(APIView):

    def get_object(self, pk):
        try:
            return Room.objects.get(pk=pk)
        except Room.DoesNotExist:
            raise NotFound

    def get(self, request, pk):
        room = self.get_object(pk)
        serializer = RoomDatailSerializer(room)
        return Response(serializer.data)

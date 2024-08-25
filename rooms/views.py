from django.conf import settings
from django.utils import timezone
from rest_framework.permissions import IsAuthenticatedOrReadOnly
from rest_framework.views import APIView
from django.db import transaction
from rest_framework.status import HTTP_204_NO_CONTENT
from rest_framework.response import Response
from rest_framework.exceptions import (
    NotFound,
    NotAuthenticated,
    ParseError,
    PermissionDenied,
)
from .models import Amenity, Room
from categories.models import Category
from .serializers import AmenitySerializer, RoomListSerializer, RoomDetailSerializer
from reviews.serializers import ReviewSerializer
from medias.serializers import PhotoSerializer
from bookings.models import Booking
from bookings.serializers import PublicBookingSerializer, CreateRoomBookingSerializer


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

    permission_classes = [IsAuthenticatedOrReadOnly]

    def get(self, request):
        all_rooms = Room.objects.all()
        serializer = RoomListSerializer(
            all_rooms,
            many=True,
            # context를 통해 serializer로 원하는 데이터 보내기
            context={"request": request},
        )
        return Response(serializer.data)

    def post(self, request):
        serializer = RoomDetailSerializer(data=request.data)
        if serializer.is_valid():
            category_pk = request.data.get("category")
            if not category_pk:
                raise ParseError("Category is required.")
            try:
                category = Category.objects.get(pk=category_pk)
                if category.kind == Category.CategoryKindChoices.EXPERIENCES:
                    raise ParseError("The category kind should be 'rooms'")
            except Category.DoesNotExist:
                raise ParseError("Category not found")
            try:
                with transaction.atomic():
                    room = serializer.save(
                        owner=request.user,
                        category=category,
                    )
                    amenities = request.data.get("amenities")
                    for amenity_pk in amenities:
                        amenity = Amenity.objects.get(pk=amenity_pk)
                        room.amenities.add(amenity)
                    serializer = RoomDetailSerializer(room)
                    return Response(serializer.data)
            except Exception:
                raise ParseError("Amenity not found")
        else:
            raise NotAuthenticated


class RoomDetail(APIView):

    permission_classes = [IsAuthenticatedOrReadOnly]

    def get_object(self, pk):
        try:
            return Room.objects.get(pk=pk)
        except Room.DoesNotExist:
            raise NotFound

    def get(self, request, pk):
        room = self.get_object(pk)
        serializer = RoomDetailSerializer(
            room,
            context={"request": request},
        )
        return Response(serializer.data)

    def put(self, request, pk):
        room = self.get_object(pk)

        if room.owner != request.user:
            raise PermissionDenied

        serializer = RoomDetailSerializer(
            room,
            data=request.data,
            partial=True,
        )

        if serializer.is_valid():
            category_pk = request.data.get("category")
            if category_pk:
                try:
                    category = Category.objects.get(pk=category_pk)
                    if category.kind == Category.CategoryKindChoices.EXPERIENCES:
                        raise ParseError("The category kind should be rooms")
                except Category.DoesNotExist:
                    raise ParseError(detail="Category not found")

            try:
                with transaction.atomic():
                    if category_pk:
                        room = serializer.save(category=category)
                    else:
                        room = serializer.save()

                    amenities = request.data.get("amenities")
                    if amenities:
                        room.amenities.clear()
                        for amenity_pk in amenities:
                            amenity = Amenity.objects.get(pk=amenity_pk)
                            room.amenities.add(amenity)
                    else:
                        room.amenities.clear()

                    return Response(RoomDetailSerializer(room).data)
            except Exception as e:
                print(e)
                raise ParseError("amenity not found")
        else:
            return Response(serializer.errors)

    def delete(self, request, pk):
        room = self.get_object(pk)
        if room.owner != request.user:
            raise PermissionDenied  # 허가거부
        room.delete()
        return Response(status=HTTP_204_NO_CONTENT)


class RoomReviews(APIView):

    permission_classes = [IsAuthenticatedOrReadOnly]

    def get_object(self, pk):
        try:
            return Room.objects.get(pk=pk)
        except Room.DoesNotExist:
            raise NotFound

    def get(self, request, pk):
        try:
            page = request.query_params.get("page", 1)
            # page의 타입을 보니 str인 것을 확인 --> int 타입으로 변환
            page = int(page)
        except ValueError:  # 오류 발생시 page 1으로 return
            page = 1
        # page size와 시작, 끝 설정
        page_size = settings.PAGE_SIZE
        start = (page - 1) * page_size
        end = start + page_size
        room = self.get_object(pk)
        serializer = ReviewSerializer(
            # 모든 리뷰를 보여주지 않고, 원하는 리뷰만 인덱스
            room.reviews.all()[start:end],
            many=True,
        )
        return Response(serializer.data)

    def post(self, request, pk):
        serializer = ReviewSerializer(data=request.data)
        if serializer.is_valid():
            review = serializer.save(
                user=request.user,
                room=self.get_object(pk),
            )
            serializer = ReviewSerializer(review)
            return Response(serializer.data)


class RoomAmenities(APIView):

    def get_object(self, pk):
        try:
            return Room.objects.get(pk=pk)
        except Room.DoesNotExist:
            raise NotFound

    def get(self, request, pk):
        try:
            page = request.query_params.get("page", 1)
            page = int(page)
        except ValueError:
            page = 1
        page_size = settings.PAGE_SIZE
        start = (page - 1) * page_size
        end = start + page_size
        room = self.get_object(pk)
        serializer = AmenitySerializer(
            room.amenities.all()[start:end],
            many=True,
        )
        return Response(serializer.data)


class RoomPhotos(APIView):

    permission_classes = [IsAuthenticatedOrReadOnly]

    def get_object(self, pk):
        try:
            return Room.objects.get(pk=pk)
        except Room.DoesNotExist:
            raise NotFound

    def post(self, request, pk):
        room = self.get_object(pk)
        if request.user != room.owner:
            raise PermissionDenied
        serializer = PhotoSerializer(data=request.data)
        if serializer.is_valid():
            photo = serializer.save(room=room)
            serializer = PhotoSerializer(photo)
            return Response(serializer.data)
        else:
            return Response(serializer.errors)


class RoomBookings(APIView):

    permission_classes = [IsAuthenticatedOrReadOnly]

    def get_object(self, pk):
        try:
            return Room.objects.get(pk=pk)
        except:
            raise NotFound

    def get(self, request, pk):
        room = self.get_object(pk)
        # 로컬서버의 시간을 가져오는 함수
        now = timezone.localtime(timezone.now()).date()
        bookings = Booking.objects.filter(
            room=room,
            kind=Booking.BookingKindChoices.ROOM,
            # 현재보다 미래의 체크인 예약만 보여주는 조건
            check_in__gt=now,
        )
        serializer = PublicBookingSerializer(bookings, many=True)
        return Response(serializer.data)

    def post(self, request, pk):
        room = self.get_object(pk)
        serializer = CreateRoomBookingSerializer(data=request.data)
        if serializer.is_valid():
            return Response({"ok": True})
        else:
            return Response(serializer.errors)

import jwt
import requests
from django.conf import settings
from django.contrib.auth import authenticate, login, logout
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework import status
from rest_framework.exceptions import ParseError, NotFound
from rest_framework.permissions import IsAuthenticated
from . import serializers
from users.models import User
from rooms.models import Room
from rooms.serializers import RoomListSerializer
from reviews.models import Review
from reviews.serializers import ReviewSerializer


class Me(APIView):

    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        serializer = serializers.PrivateUserSerializer(user)
        return Response(serializer.data)

    def put(self, request):
        user = request.user
        serializer = serializers.PrivateUserSerializer(
            user,
            data=request.data,
            partial=True,
        )
        if serializer.is_valid():
            user = serializer.save()
            serializer = serializers.PrivateUserSerializer(user)
            return Response(serializer.data)
        else:
            return Response(serializer.errors)


class Users(APIView):

    def post(self, request):
        password = request.data.get("password")
        if not password:
            raise ParseError
        serializer = serializers.PrivateUserSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            user.set_password(password)
            user.save()
            serializer = serializers.PrivateUserSerializer(user)
            return Response(serializer.data)
        else:
            return Response(serializer.errors)


class PublicUser(APIView):
    def get(self, request, username):
        try:
            user = User.objects.get(username=username)
        except User.DoesNotExist:
            raise NotFound
        serializer = serializers.PublicUserSerializer(user)
        return Response(serializer.data)


class UserRooms(APIView):
    def get(self, request, username):
        all_rooms = Room.objects.filter(owner__username=username)
        serializer = RoomListSerializer(
            all_rooms,
            many=True,
            context={"request": request},
        )
        return Response(serializer.data)


class UserReviews(APIView):
    def get(self, request, username):
        all_reviews = Review.objects.filter(user__username=username)
        serializer = ReviewSerializer(
            all_reviews,
            many=True,
        )
        return Response(serializer.data)


class ChangePassword(APIView):

    permission_classes = [IsAuthenticated]

    def put(self, request):
        user = request.user
        old_password = request.data.get("old_password")
        new_password = request.data.get("new_password")
        if not old_password or not new_password:
            raise ParseError
        if user.check_password(old_password):
            user.set_password(new_password)
            user.save()
            return Response(status=status.HTTP_200_OK)
        else:
            raise ParseError


class LogIn(APIView):
    def post(self, request):
        username = request.data.get("username")
        password = request.data.get("password")
        if not username or not password:
            raise ParseError
        user = authenticate(
            request,
            username=username,
            password=password,
        )
        if user:
            login(request, user)
            return Response({"ok": "Welcome!"})
        else:
            return Response({"error": "wrong password"})


class LogOut(APIView):

    permission_classes = [IsAuthenticated]

    def post(self, request):
        logout(request)
        return Response({"ok": "bye!"})


class JWTLogIn(APIView):

    def post(self, request):
        username = request.data.get("username")
        password = request.data.get("password")
        if not username or not password:
            raise ParseError
        user = authenticate(
            request,
            username=username,
            password=password,
        )
        if user:
            token = jwt.encode(
                {"pk": user.pk},
                settings.SECRET_KEY,
                algorithm="HS256",
            )
            return Response({"token": token})
        else:
            return Response({"error": "wrong password"})


#### 깃허브 로그인 기능 일시 중지
# class GithubLogIn(APIView):

#     def post(self, request):
#         code = request.data.get("code")
#         access_token = requests.post(
#             f"https://github.com/login/oauth/access_token?code={code}&client_id=Ov23lihjpCNDdqbvnq0l&client_secret={settings.GH_SECRET}",
#             headers={"Accept": "application/json"},
#         )

#         access_token = access_token.json().get("access_token")
#         user_data = requests.get(
#             "https://api.github.com/user",
#             headers={
#                 "Authorization": f"Bearer {access_token}",
#                 "Accept": "application/json",
#             },
#         )

#         print(user_data.json())


class KakaoLogIn(APIView):

    def post(self, request):
        try:
            code = request.data.get("code")
            access_token = requests.post(
                "https://kauth.kakao.com/oauth/token",
                headers={"Content-Type": "application/x-www-form-urlencoded"},
                data={
                    "grant_type": "authorization_code",
                    "client_id": "ce455554501dbefab816e14771d20a5c",
                    "redirect_uri": "http://127.0.0.1:3000/social/kakao",
                    "code": code,
                },
            )

            access_token = access_token.json().get("access_token")
            user_data = requests.get(
                "https://kapi.kakao.com/v2/user/me",
                headers={
                    "Authorization": f"Bearer {access_token}",
                    "Content-type": "application/x-www-form-urlencoded; charset=utf-8",
                },
            )

            user_data = user_data.json()
            kakao_account = user_data.get("kakao_account")
            profile = kakao_account.get("profile")

            kakao_id = user_data.get("id")  # Kakao 고유 ID 사용
            username = profile.get("nickname")
            avatar = profile.get("profile_image_url")

            # 이메일 없이 고유 ID로 유저 처리
            user, created = User.objects.get_or_create(
                username=kakao_id,
                defaults={
                    "name": username,
                    "avatar": avatar,
                },
            )

            if created:
                user.set_unusable_password()
                user.save()

            # 사용자 로그인 처리
            login(request, user)

            return Response(status=status.HTTP_200_OK)

        except Exception as e:
            print(f"Error: {str(e)}")  # 에러를 콘솔에 출력하여 디버깅에 도움
            return Response(status=status.HTTP_400_BAD_REQUEST)

from django.urls import path
from rest_framework.authtoken.views import obtain_auth_token
from . import views


urlpatterns = [
    path("", views.Users.as_view()),
    path("me", views.Me.as_view()),
    path("change-password", views.ChangePassword.as_view()),
    path("log-in", views.LogIn.as_view()),  # 직접 구현한 로그인
    path("log-out", views.LogOut.as_view()),  # 직접 구현한 로그아웃
    path("token-login", obtain_auth_token),  # Django Rest Framework의 토큰 인증
    path("jwt-login", views.JWTLogIn.as_view()),  # JWT를 이용한 토큰 인증
    ### 깃허브 로그인 기능 일시 중지
    # path("github", views.GithubLogIn.as_view()),
    path("kakao", views.KakaoLogIn.as_view()),
    # @는 인스타에서도 사용하니까 그냥 붙이는거.
    path("@<str:username>", views.PublicUser.as_view()),
    path("@<str:username>/rooms", views.UserRooms.as_view()),
    path("@<str:username>/reviews", views.UserReviews.as_view()),
]

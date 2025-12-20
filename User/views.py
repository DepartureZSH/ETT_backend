from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions
from rest_framework.authtoken.models import Token
from .serializers import RegisterSerializer, LoginSerializer


class LoginView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.validated_data
            token, _ = Token.objects.get_or_create(user=user)

            # --- 核心修改：封装为前端要求的结构 ---
            return Response({
                "code": 0,  # 前端 index.ts 判断成功必须为 0
                "data": {  # 实际业务数据放在 data 中
                    "token": token.key,
                    "username": user.username
                },
                "msg": "登录成功"
            }, status=status.HTTP_200_OK)

        # 失败时也建议返回 code 非 0
        return Response({
            "code": 1,
            "msg": "用户名或密码错误",
            "data": serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)


class RegisterView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            token, _ = Token.objects.get_or_create(user=user)

            # --- 核心修改：统一返回结构 ---
            return Response({
                "code": 0,
                "data": {
                    "user": serializer.data,
                    "token": token.key
                },
                "msg": "注册成功"
            }, status=status.HTTP_201_CREATED)

        return Response({
            "code": 1,
            "msg": "注册失败",
            "data": serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)
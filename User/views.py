from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions
from rest_framework.authtoken.models import Token
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from .serializers import RegisterSerializer, LoginSerializer


class LoginView(APIView):
    permission_classes = [permissions.AllowAny]
    @swagger_auto_schema(
        operation_summary="用户登录",
        operation_description="用户使用账号密码登录",
        request_body=LoginSerializer,
        responses={
            201: LoginSerializer,
            400: '用户名或密码错误',
        }
    )
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
    @swagger_auto_schema(
        operation_summary="用户注册",
        operation_description="用户使用账号密码注册",
        request_body=LoginSerializer,
        responses={
            201: RegisterSerializer,
            400: '注册失败',
        }
    )
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


class LogoutView(APIView):
    # 登出必须是已登录用户才能操作
    permission_classes = [permissions.IsAuthenticated]
    @swagger_auto_schema(
        operation_summary="用户登出",
        operation_description="用户登出现账号",
        responses={
            201: '登出成功',
            400: '登出失败',
        }
    )
    def post(self, request):
        try:
            # 1. 在后端销毁 Token
            # request.user.auth_token 会获取当前请求携带 Token 对应的记录
            request.user.auth_token.delete()

            # 2. 返回符合前端拦截器要求的成功结构
            return Response({
                "code": 0,
                "data": None,
                "msg": "登出成功"
            }, status=status.HTTP_200_OK)

        except Exception as e:
            # 即使发生异常（如 Token 已不存在），也返回 code 非 0 告知前端
            return Response({
                "code": 1,
                "msg": f"登出失败: {str(e)}",
                "data": None
            }, status=status.HTTP_400_BAD_REQUEST)
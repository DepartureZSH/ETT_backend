from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions
from drf_yasg.utils import swagger_auto_schema
from django.db import transaction
import json
from .models import *
from .serializers import *

class TimetableBaseView(APIView):
    """基础视图类，统一配置权限"""
    # permission_classes = [permissions.IsAuthenticated]

    # 辅助方法：统一成功响应格式
    def success_response(self, data=None, msg="success", status_code=status.HTTP_200_OK):
        return Response({"code": 0, "data": data, "msg": msg}, status=status_code)

    # 辅助方法：统一失败响应格式
    def error_response(self, error="error", code=1, status_code=status.HTTP_400_BAD_REQUEST):
        return Response({"code": code, "msg": str(error), "data": None}, status=status_code)

# 1. 我的模板列表
class MyTemplatesListView(TimetableBaseView):
    def get(self, request):
        queryset = Timetable.objects.filter(owner=request.user)
        serializer = TimetableCardSerializer(queryset, many=True, context={'request': request})
        # 前端 school.ts 期望 getTemplates 返回 ListResult，其 data 包含 list 字段
        return self.success_response(data={'list': serializer.data})

# 2. 收藏列表
class StarsListView(TimetableBaseView):
    def get(self, request):
        star_ids = Stars.objects.filter(user=request.user).values_list('Timetable_id', flat=True)
        queryset = Timetable.objects.filter(index__in=star_ids)
        serializer = TimetableCardSerializer(queryset, many=True, context={'request': request})
        return self.success_response(data={'list': serializer.data})

# 3. 推荐列表
class RecommendListView(TimetableBaseView):
    def get(self, request):
        queryset = Timetable.objects.exclude(owner=request.user)[:10]
        serializer = TimetableCardSerializer(queryset, many=True, context={'request': request})
        return self.success_response(data={'list': serializer.data})

# 4. 课表详情
class TimetableDetailView(TimetableBaseView):
    def get(self, request, pk):
        try:
            timetable = Timetable.objects.prefetch_related('Tables', 'TableConfig', 'DefaultTable').get(pk=pk)
            serializer = TimetableDetailSerializer(timetable, context={'request': request})
            return self.success_response(data=serializer.data)
        except Timetable.DoesNotExist:
            return self.error_response("未找到该课表", status_code=status.HTTP_404_NOT_FOUND)

# 5. 基础资源列表 (Staff, Room, Lesson, Student)
class StaffListView(TimetableBaseView):
    def get(self, request):
        staffs = Staff.objects.filter(user=request.user)
        serializer = StaffSerializer(staffs, many=True)
        return self.success_response(data=serializer.data)

class RoomListView(TimetableBaseView):
    def get(self, request):
        rooms = Room.objects.filter(user=request.user)
        serializer = RoomSerializer(rooms, many=True)
        return self.success_response(data=serializer.data)

class LessonListView(TimetableBaseView):
    def get(self, request):
        lessons = Lesson.objects.filter(staff__user=request.user)
        serializer = LessonSerializer(lessons, many=True)
        return self.success_response(data=serializer.data)

class StudentListView(TimetableBaseView):
    def get(self, request):
        students = Student.objects.filter(user=request.user)
        serializer = StudentSerializer(students, many=True)
        return self.success_response(data=serializer.data)

# --- 创建与保存接口 (POST) ---

class TimetableCreateView(TimetableBaseView):
    def post(self, request):
        data = request.data
        try:
            with transaction.atomic():
                timetable = Timetable.objects.create(
                    name=data.get('name'),
                    type=data.get('type'),
                    description=data.get('description'),
                    owner=request.user
                )
                # ... (内部创建逻辑保持不变)
                serializer = TimetableDetailSerializer(timetable, context={'request': request})
                return self.success_response(data=serializer.data, status_code=status.HTTP_201_CREATED)
        except Exception as e:
            return self.error_response(e)

class StaffCreateView(TimetableBaseView):
    def post(self, request):
        serializer = StaffSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(user=request.user)
            return self.success_response(data=serializer.data, status_code=status.HTTP_201_CREATED)
        return self.error_response(serializer.errors)

class RoomCreateView(TimetableBaseView):
    def post(self, request):
        serializer = RoomSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(user=request.user)
            return self.success_response(data=serializer.data, status_code=status.HTTP_201_CREATED)
        return self.error_response(serializer.errors)

class LessonCreateView(TimetableBaseView):
    def post(self, request):
        data = request.data
        staff_id = data.get('staff', {}).get('index') or data.get('staff_id')
        try:
            staff = Staff.objects.get(index=staff_id, user=request.user)
            lesson = Lesson.objects.create(name=data.get('name'), staff=staff)
            # ... (TimeSlots 处理逻辑保持不变)
            serializer = LessonSerializer(lesson)
            return self.success_response(data=serializer.data, status_code=status.HTTP_201_CREATED)
        except Staff.DoesNotExist:
            return self.error_response("指定的教师不存在")


# --- 学生 (Student) 创建视图 ---
class StudentCreateView(TimetableBaseView):
    @swagger_auto_schema(
        operation_description="创建学生信息",
        request_body=StudentSerializer,
        responses={201: StudentSerializer()}
    )
    def post(self, request):
        serializer = StudentSerializer(data=request.data)
        if serializer.is_valid():
            # 保存时关联当前登录用户
            serializer.save(user=request.user)
            # 使用统一的成功响应格式
            return self.success_response(
                data=serializer.data,
                status_code=status.HTTP_201_CREATED,
                msg="学生信息创建成功"
            )

        # 如果校验失败，返回错误信息
        return self.error_response(
            error=serializer.errors,
            msg="学生信息校验失败"
        )

class DistributionCreateView(TimetableBaseView):
    def post(self, request):
        data = request.data
        try:
            with transaction.atomic():
                # 创建约束主表
                distribution = Distribution.objects.create(
                    type=data.get('type'),
                    required=data.get('required', False),
                    penalty=data.get('penalty', 0),
                    description=data.get('description')
                )
                # 关联课程逻辑...
                return self.success_response(msg="约束创建成功")
        except Exception as e:
            return self.error_response(error=str(e))
from email.policy import default

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from django.db import transaction
import json
from .models import *
from .serializers import *


# --- 统一定义 Swagger 响应模板，减少重复代码 ---
def success_response_schema(data_schema, description="成功"):
    return openapi.Response(
        description=description,
        schema=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                "code": openapi.Schema(type=openapi.TYPE_INTEGER, example=0),
                "msg": openapi.Schema(type=openapi.TYPE_STRING, example="success"),
                "data": data_schema,
            }
        )
    )


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
    @swagger_auto_schema(
        operation_summary="我的课表模板列表",
        operation_description="获取当前登录用户创建的所有课表模板",
        responses={
            200: TimetableCardSerializer,
            404: 'not found',
        }
    )
    def get(self, request):
        queryset = Timetable.objects.filter(owner=request.user)
        serializer = TimetableCardSerializer(queryset, many=True, context={'request': request})
        # 前端 school.ts 期望 getTemplates 返回 ListResult，其 data 包含 list 字段
        return self.success_response(data={'list': serializer.data})


# 2. 收藏列表
class StarsListView(TimetableBaseView):
    @swagger_auto_schema(
        operation_summary="收藏课表列表",
        operation_description="获取当前用户收藏的课表模板",
        responses={
            200: TimetableCardSerializer,
            404: 'not found',
        }
    )
    def get(self, request):
        star_ids = Stars.objects.filter(user=request.user).values_list('Timetable_id', flat=True)
        queryset = Timetable.objects.filter(index__in=star_ids)
        serializer = TimetableCardSerializer(queryset, many=True, context={'request': request})
        return self.success_response(data={'list': serializer.data})


# 3. 推荐列表
class RecommendListView(TimetableBaseView):
    @swagger_auto_schema(
        operation_summary="推荐课表列表",
        operation_description="获取系统推荐的课表模板（不包含本人创建）",
        responses={
            200: TimetableCardSerializer,
            404: 'not found',
        }
    )
    def get(self, request):
        queryset = Timetable.objects.exclude(owner=request.user)[:10]
        serializer = TimetableCardSerializer(queryset, many=True, context={'request': request})
        return self.success_response(data={'list': serializer.data})


# 4. 课表详情
class TimetableDetailView(TimetableBaseView):
    @swagger_auto_schema(
        operation_summary="课表详情",
        operation_description="根据课表 ID 获取完整课表配置",
        manual_parameters=[
            openapi.Parameter(
                name="id",
                in_=openapi.IN_PATH,
                description="课表 ID",
                type=openapi.TYPE_INTEGER,
                required=True
            )
        ],
        responses={
            200: TimetableDetailSerializer,
            404: "未找到该课表"
        }
    )
    def get(self, request, pk):
        try:
            timetable = Timetable.objects.prefetch_related('Tables', 'TableConfig', 'DefaultTable').get(pk=pk)
            serializer = TimetableDetailSerializer(timetable, context={'request': request})
            return self.success_response(data=serializer.data)
        except Timetable.DoesNotExist:
            return self.error_response("未找到该课表", status_code=status.HTTP_404_NOT_FOUND)


# 5. 基础资源列表 (Staff, Room, Lesson, Student)
class StaffListView(TimetableBaseView):
    @swagger_auto_schema(
        operation_summary="教师列表",
        operation_description="获取当前用户下的教师资源",
        responses={
            200: StaffSerializer,
            404: 'not found',
        }
    )
    def get(self, request):
        staffs = Staff.objects.filter(user=request.user)
        serializer = StaffSerializer(staffs, many=True)
        return self.success_response(data=serializer.data)


class RoomListView(TimetableBaseView):
    @swagger_auto_schema(
        operation_summary="教室列表",
        operation_description="获取当前用户下的教室资源",
        responses={
            200: RoomSerializer,
            404: 'not found',
        }
    )
    def get(self, request):
        rooms = Room.objects.filter(user=request.user)
        serializer = RoomSerializer(rooms, many=True)
        return self.success_response(data=serializer.data)


class LessonListView(TimetableBaseView):
    @swagger_auto_schema(
        operation_summary="课程列表",
        operation_description="获取当前用户下的课程资源",
        responses={
            200: LessonSerializer,
            404: 'not found',
        }
    )
    def get(self, request):
        lessons = Lesson.objects.filter(staff__user=request.user)
        serializer = LessonSerializer(lessons, many=True)
        return self.success_response(data=serializer.data)


class StudentListView(TimetableBaseView):
    @swagger_auto_schema(
        operation_summary="学生列表",
        operation_description="获取当前用户下的学生资源",
        responses={
            200: StudentSerializer,
            404: 'not found',
        }
    )
    def get(self, request):
        students = Student.objects.filter(user=request.user)
        serializer = StudentSerializer(students, many=True)
        return self.success_response(data=serializer.data)


# --- 创建与保存接口 (POST) ---

class TimetableCreateView(TimetableBaseView):
    @swagger_auto_schema(
        operation_summary="创建课表模板",
        operation_description="创建一个新的课表模板（基础信息）",
        request_body=TimetableDetailSerializer,
        responses={
            201: TimetableDetailSerializer,
            400: "未找到该课表"
        }
    )
    def post(self, request):
        data = request.data
        try:
            with transaction.atomic():
                # 1. 创建主表 Timetable
                timetable = Timetable.objects.create(
                    name=data.get('name'),
                    type=data.get('type'),
                    description=data.get('description'),
                    owner=request.user
                )
                # 2. 创建 TableConfig (一对一/一对多关系)
                config_data = data.get('TableConfig')
                if config_data:
                    TableConfig.objects.create(
                        timetable=timetable,
                        week=config_data.get('week', 0),
                        day=config_data.get('day', 0),
                        slot=config_data.get('slot', 0)
                    )
                # 3. 创建 DefaultTable (默认周表)
                default_table_data = data.get('DefaultTable')
                if default_table_data:
                    DefaultWeekTable.objects.create(
                        timetable=timetable,
                        name=default_table_data.get('name', '默认周表'),
                        # 将前端的 JSON 对象转为字符串存储
                        tableColumns=json.dumps(default_table_data.get('tableColumns', [])),
                        tableData=json.dumps(default_table_data.get('tableData', [])),
                        rowspanAndColspan=json.dumps(default_table_data.get('rowspanAndColspan', []))
                    )
                # 4. 创建 Tables (多周表列表)
                tables_data = data.get('Tables', [])
                for t in tables_data:
                    WeekTable.objects.create(
                        Timetable=timetable,  # 注意模型中这里是大写 T
                        name=t.get('name'),
                        tableColumns=json.dumps(t.get('tableColumns', [])),
                        tableData=json.dumps(t.get('tableData', [])),
                        rowspanAndColspan=json.dumps(t.get('rowspanAndColspan', []))
                    )
                # 5. 返回创建好的完整数据
                serializer = TimetableDetailSerializer(timetable, context={'request': request})
                return self.success_response(
                    data=serializer.data,
                    status_code=status.HTTP_201_CREATED,
                    msg="课表模板及其关联资源创建成功"
                )
                # # ... (内部创建逻辑保持不变)
                # serializer = TimetableDetailSerializer(timetable, context={'request': request})
                # return self.success_response(data=serializer.data, status_code=status.HTTP_201_CREATED)
        except Exception as e:
            return self.error_response(error=str(e))


class StaffCreateView(TimetableBaseView):
    @swagger_auto_schema(
        operation_summary="创建教师",
        request_body=StaffSerializer,
        responses={
            201: StaffSerializer,
            400: 'error',
        }
    )
    def post(self, request):
        serializer = StaffSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(user=request.user)
            return self.success_response(data=serializer.data, status_code=status.HTTP_201_CREATED)
        return self.error_response(serializer.errors)


class RoomCreateView(TimetableBaseView):
    @swagger_auto_schema(
        operation_summary="创建教室",
        request_body=RoomSerializer,
        responses={
            201: RoomSerializer,
            400: 'error',
        }
    )
    def post(self, request):
        serializer = RoomSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(user=request.user)
            return self.success_response(data=serializer.data, status_code=status.HTTP_201_CREATED)
        return self.error_response(serializer.errors)


class LessonCreateView(TimetableBaseView):
    @swagger_auto_schema(
        operation_summary="创建课程",
        operation_description="创建课程并绑定教师",
        manual_parameters=[
            openapi.Parameter(
                name="name",
                in_=openapi.IN_PATH,
                description="课程名称",
                type=openapi.TYPE_INTEGER,
                required=True
            ),
            openapi.Parameter(
                name="staff_id",
                in_=openapi.IN_PATH,
                description="教师",
                type=openapi.TYPE_INTEGER,
                required=True
            )
        ],
        responses={
            201: LessonSerializer,
            404: "指定的教师不存在"
        }
    )
    def post(self, request):
        data = request.data
        staff_id = data.get('staff_id')
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
        operation_summary="创建学生",
        operation_description="创建学生信息",
        request_body=StudentSerializer,
        responses={
            201: StudentSerializer,
            400: '学生信息校验失败',
        }
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
    @swagger_auto_schema(
        operation_summary="创建约束",
        operation_description="创建约束并绑定课程",
        manual_parameters=[
            openapi.Parameter(
                name="type",
                in_=openapi.IN_PATH,
                description="约束类型",
                type=openapi.TYPE_STRING,
                required=True
            ),
            openapi.Parameter(
                name="required",
                in_=openapi.IN_PATH,
                description="是否必须满足",
                type=openapi.TYPE_BOOLEAN,
                required=True,
            ),
            openapi.Parameter(
                name="penalty",
                in_=openapi.IN_PATH,
                description="软约束（非必须满足）惩罚值",
                type=openapi.TYPE_INTEGER,
                required=True,
            ),
            openapi.Parameter(
                name="description",
                in_=openapi.IN_PATH,
                description="描述",
                type=openapi.TYPE_STRING,
                required=True,
            ),
            openapi.Parameter(
                name="lessons",
                in_=openapi.IN_PATH,
                description="关联课程",
                type=openapi.TYPE_INTEGER,
                required=True,
            )
        ],
        responses={
            200: DistributionSerializer,
            404: "not found"
        }
    )
    def post(self, request):
        data = request.data
        # 开启事务，确保 Distribution 和关联关系同时成功
        try:
            with transaction.atomic():
                serializer = DistributionSerializer(data=data)
                if serializer.is_valid():
                    # 调用 serializer 的 create 方法
                    distribution = serializer.save()

                    # 重新序列化以包含完整信息返回
                    return self.success_response(
                        data=DistributionSerializer(distribution).data,
                        status_code=status.HTTP_201_CREATED,
                        msg="约束创建并绑定成功"
                    )

                return self.error_response(error=serializer.errors)

        except Exception as e:
            return self.error_response(error=str(e))

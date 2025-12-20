import json
from rest_framework import serializers
from .models import *

# --- 辅助 JSON 解析逻辑 ---
class JsonTextField(serializers.Field):
    def to_representation(self, value):
        if not value: return []
        try:
            return json.loads(value)
        except:
            return value

    def to_internal_value(self, data):
        return json.dumps(data)

# --- 基础配置序列化 ---
class TableConfigSerializer(serializers.ModelSerializer):
    class Meta:
        model = TableConfig
        fields = ['week', 'day', 'slot']

class WeekTableSerializer(serializers.ModelSerializer):
    tableColumns = JsonTextField()
    tableData = JsonTextField()
    rowspanAndColspan = JsonTextField()

    class Meta:
        model = WeekTable
        fields = ['name', 'tableColumns', 'tableData', 'rowspanAndColspan']

# --- 核心：课表详情序列化 ---
class TimetableDetailSerializer(serializers.ModelSerializer):
    owner = serializers.ReadOnlyField(source='owner.username')
    TableConfig = serializers.SerializerMethodField()
    DefaultTable = serializers.SerializerMethodField()
    Tables = WeekTableSerializer(many=True, read_only=True)
    isStar = serializers.SerializerMethodField()
    usage = serializers.IntegerField(default=0)

    class Meta:
        model = Timetable
        # 注意：Timetable 模型里有 index = AutoField(primary_key=True)，所以这里可以用 index
        fields = [
            'index', 'isStar', 'owner', 'usage', 'name', 'type',
            'description', 'publishDate', 'attachment',
            'TableConfig', 'DefaultTable', 'Tables'
        ]

    def get_TableConfig(self, obj):
        config = obj.TableConfig.first()
        return TableConfigSerializer(config).data if config else None

    def get_DefaultTable(self, obj):
        default = obj.DefaultTable.first()
        return WeekTableSerializer(default).data if default else None

    def get_isStar(self, obj):
        user = self.context.get('request').user
        if user and user.is_authenticated:
            return Stars.objects.filter(user=user, Timetable=obj).exists()
        return False

class TimetableCardSerializer(serializers.ModelSerializer):
    isStar = serializers.SerializerMethodField()
    isOwner = serializers.SerializerMethodField()
    usage = serializers.SerializerMethodField()

    class Meta:
        model = Timetable
        fields = ['index', 'isStar', 'isOwner', 'usage', 'name', 'description']

    def get_isStar(self, obj):
        user = self.context.get('request').user
        if user and user.is_authenticated:
            return Stars.objects.filter(user=user, Timetable=obj).exists()
        return False

    def get_isOwner(self, obj):
        user = self.context.get('request').user
        return obj.owner == user

    def get_usage(self, obj):
        return 0

# --- 基础资源序列化 ---

class StaffSerializer(serializers.ModelSerializer):
    class Meta:
        model = Staff
        fields = '__all__'

class TimeSlotSerializer(serializers.ModelSerializer):
    class Meta:
        model = TimeSlot_Lesson
        fields = ['days', 'weeks', 'start', 'length', 'penalty']

class RoomSerializer(serializers.ModelSerializer):
    unavailable = TimeSlotSerializer(source='Timeslots', many=True, read_only=True)
    # 修正：Room 模型没定义 index，映射 id 到 index 以对接前端
    index = serializers.IntegerField(source='id', read_only=True)

    class Meta:
        model = Room
        fields = ['index', 'name', 'description', 'capacity', 'note', 'unavailable']

# 新增：补充缺失的 StudentSerializer
class StudentSerializer(serializers.ModelSerializer):
    index = serializers.IntegerField(source='id', read_only=True)

    class Meta:
        model = Student
        fields = ['index', 'name', 'description', 'note']

class LessonSerializer(serializers.ModelSerializer):
    staff = StaffSerializer(read_only=True)
    timeslots = TimeSlotSerializer(source='TimeSlots', many=True, read_only=True)
    # 修正：Lesson 模型没定义 index，映射 id 到 index
    index = serializers.IntegerField(source='id', read_only=True)

    class Meta:
        model = Lesson
        fields = ['index', 'name', 'description', 'note', 'staff', 'timeslots']
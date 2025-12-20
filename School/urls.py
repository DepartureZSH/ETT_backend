from django.urls import path
from .views import *

urlpatterns = [
    path('get-my-templates', MyTemplatesListView.as_view()),
    path('get-stars', StarsListView.as_view()),
    path('get-recommended-templates', RecommendListView.as_view()),
    path('get-details/<int:pk>', TimetableDetailView.as_view()),
    path('get-template/<int:pk>', TimetableDetailView.as_view()), # 对应前端 getTable
    path('get-rooms', RoomListView.as_view()),
    path('get-staffs', StaffListView.as_view()),
    path('get-students', StaffListView.as_view()), # 类似实现
    path('get-lessons', LessonListView.as_view()),
    # POST 接口
    path('create-timetable', TimetableCreateView.as_view()),
    path('create-staff', StaffCreateView.as_view()),
    path('create-room', RoomCreateView.as_view()),
    path('create-student', StudentCreateView.as_view()),
    path('create-lesson', LessonCreateView.as_view()),
    path('create-distribution', DistributionCreateView.as_view()),
]
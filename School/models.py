from django.db import models
from django.contrib.auth.models import User

class Timetable(models.Model):
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)
    publishDate = models.DateTimeField(auto_now=True)
    index = models.AutoField(primary_key=True)
    parentId = models.ForeignKey(
        'self',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='children',
    )
    name = models.CharField(max_length=100)
    type = models.CharField(max_length=100)
    description = models.TextField(null=True)
    attachment = models.FileField(null=True)
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name='timetables')

class DefaultWeekTable(models.Model):
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)
    name = models.CharField(max_length=100)
    tableColumns = models.TextField(null=True)
    tableData = models.TextField(null=True)
    rowspanAndColspan = models.TextField(null=True)
    timetable = models.ForeignKey(Timetable, on_delete=models.CASCADE, related_name='DefaultTable')
    class Meta:
        ordering = ['created']

class TableConfig(models.Model):
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)
    week = models.IntegerField()
    day = models.IntegerField()
    slot = models.IntegerField()
    timetable = models.ForeignKey(Timetable, on_delete=models.CASCADE, related_name='TableConfig')
    class Meta:
        ordering = ['created']

class WeekTable(models.Model):
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)
    name = models.CharField(max_length=100)
    tableColumns = models.TextField(null=True)
    tableData = models.TextField(null=True)
    rowspanAndColspan = models.TextField(null=True)
    Timetable = models.ForeignKey(Timetable, on_delete=models.CASCADE, related_name='Tables')
    class Meta:
        ordering = ['created']

class Stars(models.Model):
    created = models.DateTimeField(auto_now_add=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='Stars')
    Timetable = models.ForeignKey(Timetable, on_delete=models.CASCADE, related_name='Stars')
    class Meta:
        ordering = ['created']

class Staff(models.Model):
    index = models.IntegerField()
    created = models.DateTimeField(auto_now_add=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='Staffs')
    name = models.CharField(max_length=100)
    description = models.TextField(null=True)
    title = models.CharField(max_length=100)
    class Meta:
        ordering = ['name']

class Lesson(models.Model):
    created = models.DateTimeField(auto_now_add=True)
    name = models.CharField(max_length=100)
    description = models.TextField(null=True)
    note = models.TextField(null=True)
    staff = models.ForeignKey(Staff, on_delete=models.CASCADE, related_name='Lessons')

class TimeSlot_Lesson(models.Model):
    created = models.DateTimeField(auto_now_add=True)
    days = models.TextField()
    weeks = models.TextField()
    start = models.IntegerField()
    length = models.IntegerField()
    penalty = models.IntegerField(null=True)
    lesson = models.ForeignKey(Lesson, on_delete=models.CASCADE, related_name='TimeSlots')

class Room(models.Model):
    created = models.DateTimeField(auto_now_add=True)
    name = models.CharField(max_length=100)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='Rooms')
    description = models.TextField(null=True)
    capacity = models.IntegerField(null=True)
    note = models.TextField(null=True)
    class Meta:
        ordering = ['name']

class TimeSlot_Room(models.Model):
    created = models.DateTimeField(auto_now_add=True)
    days = models.TextField()
    weeks = models.TextField()
    start = models.IntegerField()
    length = models.IntegerField()
    penalty = models.IntegerField(null=True)
    room = models.ForeignKey(Room, on_delete=models.CASCADE, related_name='Timeslots')

class Travel(models.Model):
    created = models.DateTimeField(auto_now_add=True)
    room = models.IntegerField()
    value = models.IntegerField()
    fromRoom = models.ForeignKey(Room, on_delete=models.CASCADE, related_name='Travels')

class Lesson_opt_Room(models.Model):
    created = models.DateTimeField(auto_now_add=True)
    lesson = models.ForeignKey(Lesson, on_delete=models.CASCADE, related_name='Rooms_opt')
    room = models.ForeignKey(Room, on_delete=models.CASCADE, related_name='Lessons_opt')

class Student(models.Model):
    created = models.DateTimeField(auto_now_add=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='Students')
    name = models.CharField(max_length=100)
    description = models.TextField(null=True)
    note = models.TextField(null=True)

class Student_opt_Lesson(models.Model):
    created = models.DateTimeField(auto_now_add=True)
    lesson = models.ForeignKey(Lesson, on_delete=models.CASCADE, related_name='Students_opt')
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='Lessons_opt')

class Distribution(models.Model):
    created = models.DateTimeField(auto_now_add=True)
    type = models.CharField(max_length=100)
    required = models.BooleanField(default=False)
    penalty = models.IntegerField(null=True)
    description = models.TextField(null=True)
    note = models.TextField(null=True)

class Distribution_constraints_Lesson(models.Model):
    created = models.DateTimeField(auto_now_add=True)
    lesson = models.ForeignKey(Lesson, on_delete=models.CASCADE, related_name='Distributions')
    distribution = models.ForeignKey(Distribution, on_delete=models.CASCADE, related_name='Lessons')

class Assignment(models.Model):
    created = models.DateTimeField(auto_now_add=True)
    lesson = models.ForeignKey(Lesson, on_delete=models.CASCADE, related_name='Assignments')
    room = models.ForeignKey(Room, on_delete=models.CASCADE, related_name='Assignments')
    timeSlot = models.ForeignKey(TimeSlot_Lesson, on_delete=models.CASCADE, related_name='Assignments')

class Assignment_with_Student(models.Model):
    created = models.DateTimeField(auto_now_add=True)
    assignment = models.ForeignKey(Assignment, on_delete=models.CASCADE, related_name='Assignments_students')
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='Assignments_students')

from django.contrib import admin
from .models import Course, CoursePortion, Group, Student, Attendance, Progress, Notification

admin.site.register(Course)
admin.site.register(CoursePortion)
admin.site.register(Group)
admin.site.register(Student)
admin.site.register(Attendance)
admin.site.register(Progress)
admin.site.register(Notification)

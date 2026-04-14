from rest_framework import serializers
from django.contrib.auth.models import User
from .models import Course, CoursePortion, Topic, Group, Student, Attendance, Progress, TopicProgress, Notification


class TopicSerializer(serializers.ModelSerializer):
    class Meta:
        model = Topic
        fields = ['id', 'portion', 'title', 'description', 'order_index']


class CoursePortionSerializer(serializers.ModelSerializer):
    topics = TopicSerializer(many=True, read_only=True)
    topic_count = serializers.SerializerMethodField()

    def get_topic_count(self, obj):
        return obj.topics.count()

    class Meta:
        model = CoursePortion
        fields = ['id', 'course', 'title', 'order_index', 'topics', 'topic_count']


class CourseSerializer(serializers.ModelSerializer):
    portions = CoursePortionSerializer(many=True, read_only=True)
    student_count = serializers.SerializerMethodField()

    def get_student_count(self, obj):
        return obj.students.filter(is_active=True).count()

    class Meta:
        model = Course
        fields = ['id', 'name', 'description', 'created_at', 'portions', 'student_count']


class GroupSerializer(serializers.ModelSerializer):
    student_count = serializers.SerializerMethodField()

    def get_student_count(self, obj):
        return obj.students.filter(is_active=True).count()

    class Meta:
        model = Group
        fields = ['id', 'name', 'created_at', 'student_count']


class StudentSerializer(serializers.ModelSerializer):
    course_name = serializers.CharField(source='course.name', read_only=True)
    group_name = serializers.CharField(source='group.name', read_only=True)
    username = serializers.CharField(source='user.username', read_only=True)

    class Meta:
        model = Student
        fields = ['id', 'full_name', 'enrollment_number', 'course', 'course_name',
                  'group', 'group_name', 'primary_contact', 'whatsapp_number',
                  'secondary_contact', 'date_of_joining', 'is_active', 'username']


class AttendanceSerializer(serializers.ModelSerializer):
    student_name = serializers.CharField(source='student.full_name', read_only=True)
    enrollment_number = serializers.CharField(source='student.enrollment_number', read_only=True)

    class Meta:
        model = Attendance
        fields = ['id', 'student', 'student_name', 'enrollment_number',
                  'date', 'status', 'login_time', 'logout_time']


class ProgressSerializer(serializers.ModelSerializer):
    student_name = serializers.CharField(source='student.full_name', read_only=True)
    portion_title = serializers.CharField(source='portion.title', read_only=True)
    course_name = serializers.CharField(source='portion.course.name', read_only=True)

    class Meta:
        model = Progress
        fields = ['id', 'student', 'student_name', 'portion', 'portion_title',
                  'course_name', 'completed_on', 'updated_by']


class TopicProgressSerializer(serializers.ModelSerializer):
    student_name = serializers.CharField(source='student.full_name', read_only=True)
    topic_title = serializers.CharField(source='topic.title', read_only=True)
    portion_title = serializers.CharField(source='topic.portion.title', read_only=True)
    course_name = serializers.CharField(source='topic.portion.course.name', read_only=True)

    class Meta:
        model = TopicProgress
        fields = ['id', 'student', 'student_name', 'topic', 'topic_title',
                  'portion_title', 'course_name', 'completed_on', 'updated_by']


class NotificationSerializer(serializers.ModelSerializer):
    student_name = serializers.CharField(source='student.full_name', read_only=True)

    class Meta:
        model = Notification
        fields = ['id', 'student', 'student_name', 'type', 'message', 'sent_at', 'status', 'is_read']

from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone


class Course(models.Model):
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name


class CoursePortion(models.Model):
    """A module/chapter within a course"""
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='portions')
    title = models.CharField(max_length=200)
    order_index = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['order_index']

    def __str__(self):
        return f"{self.course.name} → {self.title}"


class Topic(models.Model):
    """A specific topic within a module/portion"""
    portion = models.ForeignKey(CoursePortion, on_delete=models.CASCADE, related_name='topics')
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    order_index = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['order_index']

    def __str__(self):
        return f"{self.portion.title} → {self.title}"


class Group(models.Model):
    name = models.CharField(max_length=200)
    created_at = models.DateField(auto_now_add=True)

    def __str__(self):
        return self.name


class Student(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='student')
    full_name = models.CharField(max_length=200)
    enrollment_number = models.CharField(max_length=50, unique=True)
    course = models.ForeignKey(Course, on_delete=models.SET_NULL, null=True, related_name='students')
    group = models.ForeignKey(Group, on_delete=models.SET_NULL, null=True, blank=True, related_name='students')
    primary_contact = models.CharField(max_length=15)
    whatsapp_number = models.CharField(max_length=15)
    secondary_contact = models.CharField(max_length=15, blank=True)
    date_of_joining = models.DateField()
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.full_name


class Attendance(models.Model):
    STATUS_CHOICES = [('present', 'Present'), ('absent', 'Absent')]
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='attendances')
    date = models.DateField()
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='absent')
    login_time = models.DateTimeField(null=True, blank=True)
    logout_time = models.DateTimeField(null=True, blank=True)

    class Meta:
        unique_together = ('student', 'date')
        ordering = ['-date']

    def __str__(self):
        return f"{self.student.full_name} - {self.date} - {self.status}"


class Progress(models.Model):
    """Track completion of a module (portion) for a student"""
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='progress_records')
    portion = models.ForeignKey(CoursePortion, on_delete=models.CASCADE, related_name='progress_records')
    completed_on = models.DateField()
    updated_by = models.CharField(max_length=100)

    class Meta:
        unique_together = ('student', 'portion')
        ordering = ['-completed_on']

    def __str__(self):
        return f"{self.student.full_name} - {self.portion.title}"


class TopicProgress(models.Model):
    """Track completion of an individual topic for a student"""
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='topic_progress')
    topic = models.ForeignKey(Topic, on_delete=models.CASCADE, related_name='student_progress')
    completed_on = models.DateField()
    updated_by = models.CharField(max_length=100)

    class Meta:
        unique_together = ('student', 'topic')
        ordering = ['-completed_on']

    def __str__(self):
        return f"{self.student.full_name} - {self.topic.title}"


class Notification(models.Model):
    TYPE_CHOICES = [('login', 'Login'), ('logout', 'Logout'), ('absent', 'Absent'), ('general', 'General')]
    STATUS_CHOICES = [('sent', 'Sent'), ('failed', 'Failed'), ('pending', 'Pending')]
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='notifications')
    type = models.CharField(max_length=10, choices=TYPE_CHOICES)
    message = models.TextField()
    sent_at = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='sent')
    is_read = models.BooleanField(default=False)

    class Meta:
        ordering = ['-sent_at']

    def __str__(self):
        return f"{self.student.full_name} - {self.type} - {self.sent_at}"

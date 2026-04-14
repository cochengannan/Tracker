from django.contrib.auth.models import User
from django.contrib.auth import authenticate
from django.utils import timezone
from django.http import HttpResponse
from django.db.models import Count, Q
from rest_framework import viewsets, status
from rest_framework.decorators import api_view, permission_classes, action
from rest_framework.permissions import IsAuthenticated, AllowAny, IsAdminUser
from rest_framework.response import Response
from rest_framework.authtoken.models import Token
from datetime import date
import io
from django.http import HttpResponse

def home(request):
    return HttpResponse("Backend is working 🚀")

from .models import Course, CoursePortion, Topic, Group, Student, Attendance, Progress, TopicProgress, Notification
from .serializers import (CourseSerializer, CoursePortionSerializer, TopicSerializer,
                           GroupSerializer, StudentSerializer, AttendanceSerializer,
                           ProgressSerializer, TopicProgressSerializer, NotificationSerializer)


# ── Auth ────────────────────────────────────────────────────────────────────

@api_view(['POST'])
@permission_classes([AllowAny])
def login_view(request):
    username = request.data.get('username', '').strip()
    password = request.data.get('password', '')
    if not username or not password:
        return Response({'error': 'Username and password required.'}, status=400)
    user = authenticate(username=username, password=password)
    if not user:
        return Response({'error': 'Invalid username or password.'}, status=401)
    token, _ = Token.objects.get_or_create(user=user)
    is_admin = user.is_staff
    student_data = None
    if not is_admin:
        try:
            student = user.student
            if not student.is_active:
                return Response({'error': 'Your account has been deactivated.'}, status=403)
            today = date.today()
            att, created = Attendance.objects.get_or_create(
                student=student, date=today,
                defaults={'status': 'present', 'login_time': timezone.now()}
            )
            if not created and att.status == 'absent':
                att.status = 'present'
                att.login_time = timezone.now()
                att.save()
            Notification.objects.create(
                student=student, type='login',
                message=f"{student.full_name} has arrived at {timezone.now().strftime('%I:%M %p')}",
                status='sent'
            )
            student_data = StudentSerializer(student).data
        except Student.DoesNotExist:
            pass
    return Response({
        'token': token.key,
        'is_admin': is_admin,
        'username': user.username,
        'student': student_data,
    })


@api_view(['POST'])
@permission_classes([AllowAny])
def register_student(request):
    """Student self-registration with custom username and password"""
    username = request.data.get('username', '').strip()
    password = request.data.get('password', '')
    full_name = request.data.get('full_name', '').strip()
    enrollment_number = request.data.get('enrollment_number', '').strip()
    course_id = request.data.get('course')
    primary_contact = request.data.get('primary_contact', '').strip()
    whatsapp_number = request.data.get('whatsapp_number', '').strip()
    secondary_contact = request.data.get('secondary_contact', '').strip()
    date_of_joining = request.data.get('date_of_joining')

    errors = {}
    if not username: errors['username'] = 'Username is required.'
    elif User.objects.filter(username=username).exists(): errors['username'] = 'This username is already taken.'
    if not password: errors['password'] = 'Password is required.'
    elif len(password) < 6: errors['password'] = 'Password must be at least 6 characters.'
    if not full_name: errors['full_name'] = 'Full name is required.'
    if not enrollment_number: errors['enrollment_number'] = 'Enrollment number is required.'
    elif Student.objects.filter(enrollment_number=enrollment_number).exists():
        errors['enrollment_number'] = 'This enrollment number is already registered.'
    if not course_id: errors['course'] = 'Course is required.'
    if not primary_contact: errors['primary_contact'] = 'Primary contact is required.'
    if not whatsapp_number: errors['whatsapp_number'] = 'WhatsApp number is required.'
    if not date_of_joining: errors['date_of_joining'] = 'Date of joining is required.'

    if errors:
        return Response({'errors': errors}, status=400)

    user = User.objects.create_user(username=username, password=password)
    student = Student.objects.create(
        user=user, full_name=full_name, enrollment_number=enrollment_number,
        course_id=course_id, primary_contact=primary_contact,
        whatsapp_number=whatsapp_number, secondary_contact=secondary_contact,
        date_of_joining=date_of_joining
    )
    return Response({'message': 'Registration successful. You can now log in.'}, status=201)


@api_view(['POST'])
def logout_view(request):
    try:
        student = request.user.student
        today = date.today()
        try:
            att = Attendance.objects.get(student=student, date=today)
            att.logout_time = timezone.now()
            att.save()
        except Attendance.DoesNotExist:
            pass
        Notification.objects.create(
            student=student, type='logout',
            message=f"{student.full_name} has left at {timezone.now().strftime('%I:%M %p')}",
            status='sent'
        )
    except Student.DoesNotExist:
        pass
    try:
        request.user.auth_token.delete()
    except Exception:
        pass
    return Response({'message': 'Logged out successfully'})


# ── Dashboard ────────────────────────────────────────────────────────────────

@api_view(['GET'])
def dashboard_stats(request):
    today = date.today()
    total_students = Student.objects.filter(is_active=True).count()
    present_today = Attendance.objects.filter(date=today, status='present').count()
    absent_today = Attendance.objects.filter(date=today, status='absent').count()
    notifications_today = Notification.objects.filter(sent_at__date=today).count()
    recent_attendance = Attendance.objects.filter(date=today).select_related('student').order_by('-login_time')[:10]
    recent_notifications = Notification.objects.all().select_related('student')[:8]
    courses = Course.objects.all()
    course_progress = []
    for c in courses:
        total = c.portions.count()
        completed = Progress.objects.filter(portion__course=c).values('portion').distinct().count()
        course_progress.append({'name': c.name, 'total': total, 'completed': completed})
    return Response({
        'total_students': total_students,
        'present_today': present_today,
        'absent_today': absent_today,
        'notifications_today': notifications_today,
        'recent_attendance': AttendanceSerializer(recent_attendance, many=True).data,
        'recent_notifications': NotificationSerializer(recent_notifications, many=True).data,
        'course_progress': course_progress,
    })


# ── Student portal ────────────────────────────────────────────────────────────

@api_view(['GET'])
def student_notifications(request):
    """Notifications for the logged-in student"""
    try:
        student = request.user.student
    except Student.DoesNotExist:
        return Response({'error': 'Not a student account'}, status=403)
    notifs = Notification.objects.filter(student=student).order_by('-sent_at')[:50]
    # Mark all as read
    Notification.objects.filter(student=student, is_read=False).update(is_read=True)
    return Response(NotificationSerializer(notifs, many=True).data)


@api_view(['GET'])
def student_unread_count(request):
    try:
        student = request.user.student
        count = Notification.objects.filter(student=student, is_read=False).count()
        return Response({'unread': count})
    except Student.DoesNotExist:
        return Response({'unread': 0})


# ── ViewSets ─────────────────────────────────────────────────────────────────

class CourseViewSet(viewsets.ModelViewSet):
    queryset = Course.objects.all()
    serializer_class = CourseSerializer

    def get_permissions(self):
        # Anyone can list/retrieve courses (needed for registration form)
        if self.action in ('list', 'retrieve'):
            return [AllowAny()]
        return [IsAuthenticated()]


class CoursePortionViewSet(viewsets.ModelViewSet):
    queryset = CoursePortion.objects.all()
    serializer_class = CoursePortionSerializer

    def get_queryset(self):
        qs = super().get_queryset()
        course_id = self.request.query_params.get('course')
        if course_id:
            qs = qs.filter(course_id=course_id)
        return qs


class TopicViewSet(viewsets.ModelViewSet):
    queryset = Topic.objects.all()
    serializer_class = TopicSerializer

    def get_queryset(self):
        qs = super().get_queryset()
        portion_id = self.request.query_params.get('portion')
        course_id = self.request.query_params.get('course')
        if portion_id:
            qs = qs.filter(portion_id=portion_id)
        if course_id:
            qs = qs.filter(portion__course_id=course_id)
        return qs


class GroupViewSet(viewsets.ModelViewSet):
    queryset = Group.objects.all()
    serializer_class = GroupSerializer

    @action(detail=True, methods=['post'])
    def bulk_progress(self, request, pk=None):
        group = self.get_object()
        portion_id = request.data.get('portion_id')
        completed_on = request.data.get('completed_on', str(date.today()))
        updated_by = request.user.username
        students = group.students.filter(is_active=True)
        created_count = 0
        for student in students:
            _, created = Progress.objects.get_or_create(
                student=student, portion_id=portion_id,
                defaults={'completed_on': completed_on, 'updated_by': updated_by}
            )
            if created:
                created_count += 1
        return Response({'message': f'Updated {created_count} students in group {group.name}'})


class StudentViewSet(viewsets.ModelViewSet):
    queryset = Student.objects.filter(is_active=True).select_related('user', 'course', 'group')
    serializer_class = StudentSerializer

    def create(self, request, *args, **kwargs):
        """Admin creates student — username and password provided by admin"""
        username = request.data.get('username', '').strip()
        password = request.data.get('password', '')
        if not username:
            return Response({'username': ['Username is required.']}, status=400)
        if not password:
            return Response({'password': ['Password is required.']}, status=400)
        if User.objects.filter(username=username).exists():
            return Response({'username': ['This username is already taken.']}, status=400)
        if Student.objects.filter(enrollment_number=request.data.get('enrollment_number', '')).exists():
            return Response({'enrollment_number': ['Enrollment number already exists.']}, status=400)
        user = User.objects.create_user(username=username, password=password)
        student = Student.objects.create(
            user=user,
            full_name=request.data.get('full_name'),
            enrollment_number=request.data.get('enrollment_number'),
            course_id=request.data.get('course') or None,
            group_id=request.data.get('group') or None,
            primary_contact=request.data.get('primary_contact', ''),
            whatsapp_number=request.data.get('whatsapp_number', ''),
            secondary_contact=request.data.get('secondary_contact', ''),
            date_of_joining=request.data.get('date_of_joining'),
        )
        return Response({'student': StudentSerializer(student).data}, status=201)

    def partial_update(self, request, *args, **kwargs):
        """PATCH — allow updating group, course, and other editable fields"""
        student = self.get_object()
        allowed = ['group', 'course', 'full_name', 'primary_contact', 'whatsapp_number', 'secondary_contact']
        for field in allowed:
            if field in request.data:
                val = request.data[field]
                if field == 'group':
                    student.group_id = val if val not in (None, '', 'null') else None
                elif field == 'course':
                    student.course_id = val if val not in (None, '', 'null') else None
                else:
                    setattr(student, field, val)
        student.save()
        return Response(StudentSerializer(student).data)

    def destroy(self, request, *args, **kwargs):
        student = self.get_object()
        student.is_active = False
        student.save()
        return Response(status=204)


class AttendanceViewSet(viewsets.ModelViewSet):
    queryset = Attendance.objects.all().select_related('student')
    serializer_class = AttendanceSerializer

    def get_queryset(self):
        qs = super().get_queryset()
        date_param = self.request.query_params.get('date')
        student_id = self.request.query_params.get('student')
        month = self.request.query_params.get('month')
        year = self.request.query_params.get('year')
        if date_param: qs = qs.filter(date=date_param)
        if student_id: qs = qs.filter(student_id=student_id)
        if month and year: qs = qs.filter(date__month=month, date__year=year)
        return qs

    @action(detail=False, methods=['post'])
    def mark_absent(self, request):
        today = date.today()
        students = Student.objects.filter(is_active=True)
        marked = 0
        for student in students:
            att, created = Attendance.objects.get_or_create(
                student=student, date=today,
                defaults={'status': 'absent'}
            )
            if created:
                Notification.objects.create(
                    student=student, type='absent',
                    message=f"{student.full_name} was absent on {today}. Please contact us.",
                    status='sent'
                )
                marked += 1
        return Response({'marked_absent': marked})


class ProgressViewSet(viewsets.ModelViewSet):
    queryset = Progress.objects.all().select_related('student', 'portion', 'portion__course')
    serializer_class = ProgressSerializer

    def get_queryset(self):
        qs = super().get_queryset()
        student_id = self.request.query_params.get('student')
        course_id = self.request.query_params.get('course')
        if student_id: qs = qs.filter(student_id=student_id)
        if course_id: qs = qs.filter(portion__course_id=course_id)
        return qs

    def perform_create(self, serializer):
        serializer.save(updated_by=self.request.user.username)


class TopicProgressViewSet(viewsets.ModelViewSet):
    queryset = TopicProgress.objects.all().select_related('student', 'topic', 'topic__portion', 'topic__portion__course')
    serializer_class = TopicProgressSerializer

    def get_queryset(self):
        qs = super().get_queryset()
        student_id = self.request.query_params.get('student')
        topic_id = self.request.query_params.get('topic')
        portion_id = self.request.query_params.get('portion')
        course_id = self.request.query_params.get('course')
        if student_id: qs = qs.filter(student_id=student_id)
        if topic_id: qs = qs.filter(topic_id=topic_id)
        if portion_id: qs = qs.filter(topic__portion_id=portion_id)
        if course_id: qs = qs.filter(topic__portion__course_id=course_id)
        return qs

    def perform_create(self, serializer):
        serializer.save(updated_by=self.request.user.username)

    def create(self, request, *args, **kwargs):
        # Allow bulk: list of topic IDs
        topic_ids = request.data.get('topic_ids')
        if topic_ids:
            student_id = request.data.get('student')
            completed_on = request.data.get('completed_on', str(date.today()))
            created_count = 0
            for tid in topic_ids:
                _, created = TopicProgress.objects.get_or_create(
                    student_id=student_id, topic_id=tid,
                    defaults={'completed_on': completed_on, 'updated_by': request.user.username}
                )
                if created: created_count += 1
            return Response({'created': created_count}, status=201)
        return super().create(request, *args, **kwargs)


class NotificationViewSet(viewsets.ModelViewSet):
    queryset = Notification.objects.all().select_related('student')
    serializer_class = NotificationSerializer
    http_method_names = ['get', 'delete', 'patch']

    def get_queryset(self):
        qs = super().get_queryset()
        student_id = self.request.query_params.get('student')
        ntype = self.request.query_params.get('type')
        if student_id: qs = qs.filter(student_id=student_id)
        if ntype: qs = qs.filter(type=ntype)
        return qs


# ── Reports ───────────────────────────────────────────────────────────────────

@api_view(['GET'])
def generate_report(request):
    from reportlab.lib.pagesizes import A4
    from reportlab.lib import colors
    from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import inch

    student_id = request.query_params.get('student')
    month = request.query_params.get('month', date.today().month)
    year = request.query_params.get('year', date.today().year)

    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, topMargin=0.5*inch, bottomMargin=0.5*inch)
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle('Title', parent=styles['Title'], fontSize=18, textColor=colors.HexColor('#1a1a2e'))
    heading_style = ParagraphStyle('Heading', parent=styles['Heading2'], fontSize=13, textColor=colors.HexColor('#16213e'))
    story = []
    story.append(Paragraph("Student Progress Tracker", title_style))
    story.append(Paragraph(f"Report — {date(int(year), int(month), 1).strftime('%B %Y')}", styles['Normal']))
    story.append(Spacer(1, 20))

    students = Student.objects.filter(id=student_id, is_active=True) if student_id else Student.objects.filter(is_active=True).select_related('course')

    for student in students:
        story.append(Paragraph(student.full_name, heading_style))
        story.append(Paragraph(f"Enrollment: {student.enrollment_number} | Course: {student.course.name if student.course else 'N/A'}", styles['Normal']))
        story.append(Spacer(1, 8))
        att_records = Attendance.objects.filter(student=student, date__month=month, date__year=year).order_by('date')
        if att_records.exists():
            present_count = att_records.filter(status='present').count()
            att_data = [['Date', 'Status', 'Login', 'Logout']]
            for att in att_records:
                login = att.login_time.strftime('%I:%M %p') if att.login_time else '—'
                logout = att.logout_time.strftime('%I:%M %p') if att.logout_time else '—'
                att_data.append([str(att.date), att.status.capitalize(), login, logout])
            att_table = Table(att_data, colWidths=[1.5*inch, 1.2*inch, 1.5*inch, 1.5*inch])
            att_table.setStyle(TableStyle([
                ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#1a1a2e')),
                ('TEXTCOLOR', (0,0), (-1,0), colors.white),
                ('FONTSIZE', (0,0), (-1,-1), 9),
                ('GRID', (0,0), (-1,-1), 0.5, colors.grey),
                ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, colors.HexColor('#f5f5f5')]),
            ]))
            story.append(Paragraph(f"Attendance ({present_count}/{att_records.count()} days present)", styles['Heading3']))
            story.append(att_table)
            story.append(Spacer(1, 10))
        # Topic progress
        tp_records = TopicProgress.objects.filter(student=student).select_related('topic', 'topic__portion').order_by('topic__portion__order_index', 'topic__order_index')
        if tp_records.exists():
            tp_data = [['Module', 'Topic', 'Completed On']]
            for tp in tp_records:
                tp_data.append([tp.topic.portion.title, tp.topic.title, str(tp.completed_on)])
            tp_table = Table(tp_data, colWidths=[2*inch, 2.5*inch, 1.2*inch])
            tp_table.setStyle(TableStyle([
                ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#0f3460')),
                ('TEXTCOLOR', (0,0), (-1,0), colors.white),
                ('FONTSIZE', (0,0), (-1,-1), 9),
                ('GRID', (0,0), (-1,-1), 0.5, colors.grey),
                ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, colors.HexColor('#f5f5f5')]),
            ]))
            story.append(Paragraph(f"Topic Progress ({tp_records.count()} topics completed)", styles['Heading3']))
            story.append(tp_table)
        story.append(Spacer(1, 24))

    doc.build(story)
    buffer.seek(0)
    response = HttpResponse(buffer, content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="report_{month}_{year}.pdf"'
    return response

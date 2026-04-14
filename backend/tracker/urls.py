from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register('courses', views.CourseViewSet)
router.register('portions', views.CoursePortionViewSet)
router.register('topics', views.TopicViewSet)
router.register('groups', views.GroupViewSet)
router.register('students', views.StudentViewSet)
router.register('attendance', views.AttendanceViewSet)
router.register('progress', views.ProgressViewSet)
router.register('topic-progress', views.TopicProgressViewSet)
router.register('notifications', views.NotificationViewSet)

urlpatterns = [
    path('', include(router.urls)),
    path('auth/login/', views.login_view),
    path('auth/logout/', views.logout_view),
    path('auth/register/', views.register_student),
    path('dashboard/stats/', views.dashboard_stats),
    path('my/notifications/', views.student_notifications),
    path('my/unread/', views.student_unread_count),
    path('reports/generate/', views.generate_report),
]
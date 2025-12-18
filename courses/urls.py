from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    StudentViewSet, CourseViewSet, EnrollmentViewSet, GradeViewSet,
    ProfessorLoginView, ProfessorDashboardView, StudentCreateView, CourseDetailView,
    enroll_student_view, submit_grade_api
)
from django.contrib.auth.views import LogoutView

router = DefaultRouter()
router.register(r'students', StudentViewSet)
router.register(r'courses', CourseViewSet)
router.register(r'grades', GradeViewSet)

urlpatterns = [
    path('', include(router.urls)),
    path('enroll/', EnrollmentViewSet.as_view({'post': 'create'}), name='enroll-student'),
]


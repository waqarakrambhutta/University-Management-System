from django.urls import path
from .views import (
    ProfessorLoginView, ProfessorDashboardView, StudentCreateView, CourseDetailView,
    enroll_student_view, submit_grade_api
)
from django.contrib.auth.views import LogoutView

urlpatterns = [
    path('login/', ProfessorLoginView.as_view(), name='login'),
    path('logout/', LogoutView.as_view(), name='logout'),
    path('dashboard/', ProfessorDashboardView.as_view(), name='professor-dashboard'),
    path('students/new/', StudentCreateView.as_view(), name='student-create'),
    path('courses/<int:pk>/', CourseDetailView.as_view(), name='course-detail'),
    path('courses/<int:course_id>/enroll/', enroll_student_view, name='enroll-student-view'),
    
    # Helper API for frontend (keep here or use main API? keep here for now)
    path('api/grades/', submit_grade_api, name='submit-grade-api'),
]

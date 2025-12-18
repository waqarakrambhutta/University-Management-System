from rest_framework import viewsets, status, generics, permissions
from rest_framework.response import Response
from rest_framework.decorators import action
from django.db import transaction
from django.shortcuts import get_object_or_404
from .models import Student, Course, Enrollment, Grade, GradeAudit, User
from .serializers import StudentSerializer, CourseSerializer, EnrollmentSerializer, GradeSerializer, GradeAuditSerializer

class IsProfessorOrAdmin(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and (
            request.user.role == User.Role.PROFESSOR or request.user.role == User.Role.ADMIN or request.user.is_staff
        )

class IsProfessor(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role == User.Role.PROFESSOR

class StudentViewSet(viewsets.ModelViewSet):
    queryset = Student.objects.all()
    serializer_class = StudentSerializer
    permission_classes = [IsProfessorOrAdmin]

class CourseViewSet(viewsets.ModelViewSet):
    queryset = Course.objects.all()
    serializer_class = CourseSerializer
    permission_classes = [permissions.IsAuthenticated] 

class EnrollmentViewSet(viewsets.ViewSet):
    permission_classes = [IsProfessor]

    def create(self, request):
        student_id = request.data.get('student')
        course_id = request.data.get('course')

        if not student_id or not course_id:
            return Response({'error': 'Student and Course are required.'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            with transaction.atomic():
 
                course = Course.objects.select_for_update().get(pk=course_id)
                
                if course.enrollments.count() >= course.capacity:
                    return Response({'error': 'Course is full.'}, status=status.HTTP_400_BAD_REQUEST)
                
                student = get_object_or_404(Student, pk=student_id)
                
                # Check if already enrolled
                if Enrollment.objects.filter(student=student, course=course).exists():
                     return Response({'error': 'Student already enrolled.'}, status=status.HTTP_400_BAD_REQUEST)

                enrollment = Enrollment.objects.create(student=student, course=course)
                serializer = EnrollmentSerializer(enrollment)
                return Response(serializer.data, status=status.HTTP_201_CREATED)

        except Course.DoesNotExist:
            return Response({'error': 'Course not found.'}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

class GradeViewSet(viewsets.ModelViewSet):
    queryset = Grade.objects.all()
    serializer_class = GradeSerializer
    permission_classes = [IsProfessorOrAdmin]

    def perform_create(self, serializer):
        # Create Grade
        grade = serializer.save(graded_by=self.request.user)
        # Audit Log
        GradeAudit.objects.create(
            grade_obj=grade,
            new_grade=grade.grade,
            changed_by=self.request.user
        )

    def perform_update(self, serializer):
        instance = serializer.instance
        previous_grade = instance.grade
        
        # Update Grade
        grade = serializer.save(graded_by=self.request.user)
        
        # Audit Log
        GradeAudit.objects.create(
            grade_obj=grade,
            previous_grade=previous_grade,
            new_grade=grade.grade,
            changed_by=self.request.user
        )

# --- Frontend Views ---

from django.contrib.auth.views import LoginView
from django.urls import reverse_lazy
from django.views.generic import ListView, DetailView, CreateView
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.shortcuts import redirect
from django.contrib import messages
import json
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_exempt

class ProfessorLoginView(LoginView):
    template_name = 'courses/login.html'
    redirect_authenticated_user = True
    
    def get_success_url(self):
        return reverse_lazy('professor-dashboard')

class ProfessorDashboardView(LoginRequiredMixin, UserPassesTestMixin, ListView):
    model = Course
    template_name = 'courses/dashboard.html'
    context_object_name = 'courses'

    def test_func(self):
        return self.request.user.role == User.Role.PROFESSOR or self.request.user.is_superuser

    def get_queryset(self):
        # Using select_related/prefetch_related for optimization
        # Since Enrollment is not directly on Course but via Reverse relation
        return Course.objects.all().prefetch_related('enrollments')

class StudentCreateView(LoginRequiredMixin, UserPassesTestMixin, CreateView):
    model = Student
    fields = ['name', 'email', 'student_id']
    template_name = 'courses/student_form.html'
    success_url = reverse_lazy('professor-dashboard')

    def test_func(self):
        return self.request.user.role == User.Role.PROFESSOR or self.request.user.is_superuser

    def form_valid(self, form):
        messages.success(self.request, "Student created successfully.")
        return super().form_valid(form)

class CourseDetailView(LoginRequiredMixin, UserPassesTestMixin, DetailView):
    model = Course
    template_name = 'courses/course_detail.html'

    def test_func(self):
        return self.request.user.role == User.Role.PROFESSOR or self.request.user.is_superuser

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['enrollments'] = self.object.enrollments.select_related('student', 'grade').all()
        # For the dropdown
        # Exclude already enrolled students could be a nice touch, but simple all() for now
        context['all_students'] = Student.objects.exclude(enrollments__course=self.object)
        return context

@require_POST
def enroll_student_view(request, course_id):
    if not request.user.is_authenticated or request.user.role != User.Role.PROFESSOR:
        messages.error(request, "Unauthorized")
        return redirect('professor-dashboard')

    student_id = request.POST.get('student_id')
    course = get_object_or_404(Course, pk=course_id)
    student = get_object_or_404(Student, pk=student_id)

    try:
        with transaction.atomic():
            course_lock = Course.objects.select_for_update().get(pk=course_id)
            if course_lock.enrollments.count() >= course_lock.capacity:
                messages.error(request, "Course is full.")
            elif Enrollment.objects.filter(student=student, course=course).exists():
                messages.error(request, "Student already enrolled.")
            else:
                Enrollment.objects.create(student=student, course=course)
                messages.success(request, f"Enrolled {student.name} successfully.")
    except Exception as e:
        messages.error(request, f"Error: {e}")

    return redirect('course-detail', pk=course_id)

@require_POST
def submit_grade_api(request):
    """
    Helper API for the frontend JS to submit/update grades easily.
    Expects JSON: { enrollment: id, grade: value }
    """
    if not request.user.is_authenticated or request.user.role != User.Role.PROFESSOR:
        return JsonResponse({'error': 'Unauthorized'}, status=403)

    try:
        data = json.loads(request.body)
        enrollment_id = data.get('enrollment')
        grade_value = data.get('grade')
        
        enrollment = get_object_or_404(Enrollment, pk=enrollment_id)
        
        # Check if grade exists
        grade_obj, created = Grade.objects.get_or_create(enrollment=enrollment, defaults={'grade': grade_value, 'graded_by': request.user})
        
        if not created:
            # Update existing
            previous_grade = grade_obj.grade
            grade_obj.grade = grade_value
            grade_obj.graded_by = request.user
            grade_obj.save()
            
            # Audit manual check (signals or override save would affect this, but our ViewSet had the audit logic)
            # Since we are modifying directly, we should manually invoke Audit or use a Service layer.
            # Reuse the Logic from the ViewSet???
            # Or just Quick create audit here.
            GradeAudit.objects.create(
                grade_obj=grade_obj,
                previous_grade=previous_grade,
                new_grade=grade_value,
                changed_by=request.user
            )
        else:
             # Audit for create
             GradeAudit.objects.create(
                grade_obj=grade_obj,
                new_grade=grade_value,
                changed_by=request.user
            )

        return JsonResponse({'status': 'success'})
    except Exception as e:
         return JsonResponse({'error': str(e)}, status=400)


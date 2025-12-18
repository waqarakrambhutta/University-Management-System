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
                # Lock the course row to prevent race conditions
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

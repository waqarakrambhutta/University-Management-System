from rest_framework import serializers
from .models import User, Student, Course, Enrollment, Grade, GradeAudit

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'role']

class StudentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Student
        fields = '__all__'

class CourseSerializer(serializers.ModelSerializer):
    class Meta:
        model = Course
        fields = '__all__'

class EnrollmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Enrollment
        fields = '__all__'
        read_only_fields = ['enrolled_at']

class GradeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Grade
        fields = ['id', 'enrollment', 'grade', 'graded_by', 'updated_at']
        read_only_fields = ['graded_by', 'updated_at']

class GradeAuditSerializer(serializers.ModelSerializer):
    class Meta:
        model = GradeAudit
        fields = '__all__'

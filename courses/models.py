from decimal import Decimal
from django.db import models
from django.contrib.auth.models import AbstractUser
from django.core.validators import MinValueValidator, MaxValueValidator
from django.conf import settings

class User(AbstractUser):
    class Role(models.TextChoices):
        PROFESSOR = 'PROFESSOR', 'Professor'
        ADMIN = 'ADMIN', 'Admin'

    role = models.CharField(max_length=20, choices=Role.choices, default=Role.ADMIN)

class Student(models.Model):
    name = models.CharField(max_length=255)
    email = models.EmailField(unique=True)
    student_id = models.CharField(max_length=20, unique=True)
    
    def __str__(self):
        return f"{self.name} ({self.student_id})"

class Course(models.Model):
    name = models.CharField(max_length=255)
    code = models.CharField(max_length=20, unique=True)
    capacity = models.PositiveIntegerField(default=400, validators=[MaxValueValidator(400)])
    description = models.TextField(blank=True)

    def __str__(self):
        return f"{self.code} - {self.name}"

class Enrollment(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='enrollments')
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='enrollments')
    enrolled_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('student', 'course')

    def __str__(self):
        return f"{self.student} enrolled in {self.course}"

class Grade(models.Model):
    enrollment = models.OneToOneField(Enrollment, on_delete=models.CASCADE, related_name='grade')
    grade = models.DecimalField(max_digits=5, decimal_places=2, validators=[MinValueValidator(Decimal('0.00')), MaxValueValidator(Decimal('100.00'))])
    graded_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Grade for {self.enrollment}: {self.grade}"

class GradeAudit(models.Model):
    grade_obj = models.ForeignKey(Grade, on_delete=models.CASCADE, related_name='audits')
    previous_grade = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    new_grade = models.DecimalField(max_digits=5, decimal_places=2)
    changed_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)
    changed_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Audit for {self.grade_obj} at {self.changed_at}"

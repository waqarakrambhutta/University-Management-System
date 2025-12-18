from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User, Student, Course, Enrollment, Grade, GradeAudit

# Register your models here.

@admin.register(User)
class CustomUserAdmin(UserAdmin):
    list_display = ('username', 'email', 'role', 'is_staff')
    list_filter = ('role', 'is_staff', 'is_superuser')
    fieldsets = UserAdmin.fieldsets + (
        ('Role Info', {'fields': ('role',)}),
    )

@admin.register(Student)
class StudentAdmin(admin.ModelAdmin):
    list_display = ('name', 'email', 'student_id')
    search_fields = ('name', 'email', 'student_id')

@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    list_display = ('code', 'name', 'capacity')
    search_fields = ('code', 'name')

@admin.register(Enrollment)
class EnrollmentAdmin(admin.ModelAdmin):
    list_display = ('student', 'course', 'enrolled_at')
    list_filter = ('course', 'enrolled_at')
    search_fields = ('student__name', 'course__code')

@admin.register(Grade)
class GradeAdmin(admin.ModelAdmin):
    list_display = ('enrollment', 'grade', 'graded_by', 'updated_at')
    list_filter = ('graded_by', 'updated_at')
    search_fields = ('enrollment__student__name', 'enrollment__course__code')

@admin.register(GradeAudit)
class GradeAuditAdmin(admin.ModelAdmin):
    list_display = ('grade_obj', 'previous_grade', 'new_grade', 'changed_by', 'changed_at')
    list_filter = ('changed_by', 'changed_at')
    readonly_fields = ('grade_obj', 'previous_grade', 'new_grade', 'changed_by', 'changed_at')

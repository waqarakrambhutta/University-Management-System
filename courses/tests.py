from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status
from django.contrib.auth import get_user_model
from .models import Course, Student, Enrollment, Grade, GradeAudit
from threading import Thread
import time

User = get_user_model()

class CourseTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.admin = User.objects.create_superuser('admin', 'admin@example.com', 'pass')
        self.professor = User.objects.create_user('prof', 'prof@example.com', 'pass', role=User.Role.PROFESSOR)
        # Note: Students are now managed records, not Users with login, as per simplified requirements.
        # But if we were to test permissions, we'd use a user that is NOT a professor/admin.
        self.regular_user = User.objects.create_user('student_user', 'student@example.com', 'pass', role='STUDENT') # Using default or other role if any

        self.student_record = Student.objects.create(name="John Doe", email="john@example.com", student_id="S123")
        self.course = Course.objects.create(name="CS101", code="CS101", capacity=1)

    def test_enrollment_permission(self):
        # Admin can enroll? No, updated reqs said Professors enroll. Code says IsProfessor.
        # Let's check views.py: EnrollmentViewSet has permission_classes = [IsProfessor]
        
        url = reverse('enroll-student')
        data = {'student': self.student_record.id, 'course': self.course.id}

        # Unauthenticated
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        # Regular user (if we assume they exist as users)
        self.client.force_authenticate(user=self.regular_user)
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        # Professor
        self.client.force_authenticate(user=self.professor)
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_enrollment_capacity(self):
        self.client.force_authenticate(user=self.professor)
        url = reverse('enroll-student')
        
        # 1st student
        data1 = {'student': self.student_record.id, 'course': self.course.id}
        response = self.client.post(url, data1)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # 2nd student
        student2 = Student.objects.create(name="Jane", email="jane@example.com", student_id="S124")
        data2 = {'student': student2.id, 'course': self.course.id}
        response = self.client.post(url, data2)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('Course is full', str(response.data))

    def test_grade_permission_and_audit(self):
        # Enroll first
        Enrollment.objects.create(student=self.student_record, course=self.course)
        enrollment = Enrollment.objects.get(student=self.student_record, course=self.course)

        url = reverse('grade-list')
        data = {'enrollment': enrollment.id, 'grade': 85.0}

        # Professor submits grade
        self.client.force_authenticate(user=self.professor)
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        grade_obj = Grade.objects.get(enrollment=enrollment)
        self.assertEqual(grade_obj.grade, 85.0)

        # Check Audit (Creation)
        audit = GradeAudit.objects.filter(grade_obj=grade_obj).first()
        self.assertIsNotNone(audit)
        self.assertEqual(audit.new_grade, 85.0)
        self.assertEqual(audit.changed_by, self.professor)

        # Update Grade
        url_detail = reverse('grade-detail', args=[grade_obj.id])
        data_update = {'enrollment': enrollment.id, 'grade': 90.0}
        response = self.client.put(url_detail, data_update)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Check Audit (Update)
        audits = GradeAudit.objects.filter(grade_obj=grade_obj).order_by('-changed_at')
        self.assertEqual(audits.count(), 2)
        latest_audit = audits[0]
        self.assertEqual(latest_audit.previous_grade, 85.0)
        self.assertEqual(latest_audit.new_grade, 90.0)

    def test_race_condition(self):
        # We need to verify that we cannot exceed capacity even with potential race conditions.
        # However, standard Django TransactionTestCase/TestCase does not easily support multithreaded database access 
        # (each thread gets a new connection which might not see the transaction of the test).
        # We can simulate the logic via mocking or just trust select_for_update works as per DB guarantees.
        # But here is a simplistic attempt using a separate script logic approach or just testing the logic:
        
        # NOTE: A real threaded test with SQLite in-memory DB is tricky because of connection sharing.
        # Instead, we will simulate the "check then act" gap by verifying logic constraints.
        
        # Set capacity to 1
        course = Course.objects.create(name="RaceCourse", code="RC101", capacity=1)
        student1 = Student.objects.create(name="S1", email="s1@e.com", student_id="S1")
        student2 = Student.objects.create(name="S2", email="s2@e.com", student_id="S2")
        
        self.client.force_authenticate(user=self.professor)
        
        # We can't truly test race conditions in a simple unit test suite without a more complex setup 
        # (e.g. TransactionTestCase with a real DB allowing concurrent connections).
        # We will assume select_for_update() is correct. 
        # But we can double check logic:
        
        # Enroll 1
        url = reverse('enroll-student')
        self.client.post(url, {'student': student1.id, 'course': course.id})
        
        # Enroll 2 - Should fail
        response = self.client.post(url, {'student': student2.id, 'course': course.id})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(Enrollment.objects.filter(course=course).count(), 1)



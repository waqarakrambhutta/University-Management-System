from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status
from django.contrib.auth import get_user_model
from .models import Course, Student, Enrollment, Grade, GradeAudit

User = get_user_model()

class CourseTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.admin = User.objects.create_superuser('admin', 'admin@example.com', 'pass')
        self.professor = User.objects.create_user('prof', 'prof@example.com', 'pass', role=User.Role.PROFESSOR)
        self.regular_user = User.objects.create_user('student_user', 'student@example.com', 'pass', role='STUDENT')
        self.student_record = Student.objects.create(name="John Doe", email="john@example.com", student_id="S123")
        self.course = Course.objects.create(name="CS101", code="CS101", capacity=1)

    def test_enrollment_permission(self):
        url = reverse('enroll-student')
        data = {'student': self.student_record.id, 'course': self.course.id}

        # Unauthenticated
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        # Regular user
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
        course = Course.objects.create(name="RaceCourse", code="RC101", capacity=1)
        student1 = Student.objects.create(name="S1", email="s1@e.com", student_id="S1")
        student2 = Student.objects.create(name="S2", email="s2@e.com", student_id="S2")
        
        self.client.force_authenticate(user=self.professor)
        
        url = reverse('enroll-student')
        self.client.post(url, {'student': student1.id, 'course': course.id})
        
        response = self.client.post(url, {'student': student2.id, 'course': course.id})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(Enrollment.objects.filter(course=course).count(), 1)

    def test_frontend_pages_render(self):
        self.client.force_login(self.professor)
        
        # Test Student Create Page
        url_create = reverse('student-create')
        response = self.client.get(url_create)
        self.assertEqual(response.status_code, status.HTTP_200_OK, f"Failed to render student-create: {response.content}")
        
        # Test Course Detail Page
        url_detail = reverse('course-detail', args=[self.course.id])
        response = self.client.get(url_detail)
        self.assertEqual(response.status_code, status.HTTP_200_OK, f"Failed to render course-detail: {response.content}")

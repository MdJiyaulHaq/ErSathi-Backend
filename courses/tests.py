"""
Tests for the courses app.

Covers:
- Core business rules
- Authorization boundaries
- Enrollment and completion logic
- Async task triggering
"""

from unittest.mock import patch
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APITestCase, APIClient

from core.models import User
from .models import Course, Lesson, Enrollment, LessonCompletion


class UserFactory:
    """Helper to create test users."""

    @staticmethod
    def create_instructor(email="instructor@test.com", password="testpass123"):
        return User.objects.create_user(
            username=email.split("@")[0],
            email=email,
            password=password,
            first_name="Test",
            last_name="Instructor",
            role=User.Role.INSTRUCTOR,
        )

    @staticmethod
    def create_student(email="student@test.com", password="testpass123"):
        return User.objects.create_user(
            username=email.split("@")[0],
            email=email,
            password=password,
            first_name="Test",
            last_name="Student",
            role=User.Role.STUDENT,
        )


# =============================================================================
# MODEL TESTS
# =============================================================================


class UserModelTests(TestCase):
    """Tests for User model with roles."""

    def test_create_student(self):
        """Test creating a student user."""
        user = UserFactory.create_student()
        self.assertEqual(user.role, User.Role.STUDENT)
        self.assertTrue(user.is_student)
        self.assertFalse(user.is_instructor)

    def test_create_instructor(self):
        """Test creating an instructor user."""
        user = UserFactory.create_instructor()
        self.assertEqual(user.role, User.Role.INSTRUCTOR)
        self.assertTrue(user.is_instructor)
        self.assertFalse(user.is_student)

    def test_default_role_is_student(self):
        """Test that default role is student."""
        user = User.objects.create_user(
            username="default",
            email="default@test.com",
            password="testpass123",
        )
        self.assertEqual(user.role, User.Role.STUDENT)


class CourseModelTests(TestCase):
    """Tests for Course model."""

    def setUp(self):
        self.instructor = UserFactory.create_instructor()

    def test_course_created_as_draft(self):
        """Test that courses are created in draft state."""
        course = Course.objects.create(
            instructor=self.instructor,
            title="Test Course",
            description="Test description",
        )
        self.assertFalse(course.is_published)

    def test_course_total_lessons(self):
        """Test total_lessons property."""
        course = Course.objects.create(
            instructor=self.instructor,
            title="Test Course",
        )
        Lesson.objects.create(course=course, title="Lesson 1", content="Content", order=1)
        Lesson.objects.create(course=course, title="Lesson 2", content="Content", order=2)

        self.assertEqual(course.total_lessons, 2)


class LessonModelTests(TestCase):
    """Tests for Lesson model."""

    def setUp(self):
        self.instructor = UserFactory.create_instructor()
        self.course = Course.objects.create(
            instructor=self.instructor,
            title="Test Course",
        )

    def test_lessons_ordered_by_order_field(self):
        """Test that lessons are returned in correct order."""
        Lesson.objects.create(course=self.course, title="Lesson 3", content="C", order=3)
        Lesson.objects.create(course=self.course, title="Lesson 1", content="A", order=1)
        Lesson.objects.create(course=self.course, title="Lesson 2", content="B", order=2)

        lessons = list(self.course.lessons.all())
        self.assertEqual(lessons[0].order, 1)
        self.assertEqual(lessons[1].order, 2)
        self.assertEqual(lessons[2].order, 3)

    def test_unique_order_per_course(self):
        """Test that order is unique within a course."""
        Lesson.objects.create(course=self.course, title="Lesson 1", content="A", order=1)

        with self.assertRaises(Exception):
            Lesson.objects.create(course=self.course, title="Lesson 2", content="B", order=1)


class EnrollmentModelTests(TestCase):
    """Tests for Enrollment model."""

    def setUp(self):
        self.instructor = UserFactory.create_instructor()
        self.student = UserFactory.create_student()
        self.course = Course.objects.create(
            instructor=self.instructor,
            title="Test Course",
            is_published=True,
        )
        Lesson.objects.create(course=self.course, title="Lesson 1", content="A", order=1)
        Lesson.objects.create(course=self.course, title="Lesson 2", content="B", order=2)

    def test_enrollment_unique_per_student_course(self):
        """Test that a student cannot enroll twice in the same course."""
        Enrollment.objects.create(student=self.student, course=self.course)

        with self.assertRaises(Exception):
            Enrollment.objects.create(student=self.student, course=self.course)

    def test_completion_percentage(self):
        """Test completion percentage calculation."""
        enrollment = Enrollment.objects.create(student=self.student, course=self.course)

        self.assertEqual(enrollment.completion_percentage, 0)

        lesson = self.course.lessons.first()
        LessonCompletion.objects.create(enrollment=enrollment, lesson=lesson)

        self.assertEqual(enrollment.completion_percentage, 50.0)

    def test_completion_percentage_empty_course(self):
        """Test completion percentage for course with no lessons."""
        empty_course = Course.objects.create(
            instructor=self.instructor,
            title="Empty Course",
            is_published=True,
        )
        enrollment = Enrollment.objects.create(student=self.student, course=empty_course)

        self.assertEqual(enrollment.completion_percentage, 0)


# =============================================================================
# API TESTS - COURSES
# =============================================================================


class CourseAPITests(APITestCase):
    """Tests for Course API endpoints."""

    def setUp(self):
        self.instructor = UserFactory.create_instructor()
        self.student = UserFactory.create_student()
        self.other_instructor = UserFactory.create_instructor(email="other@test.com")
        self.client = APIClient()

    def test_unauthenticated_access_denied(self):
        """Test that unauthenticated users cannot access courses."""
        response = self.client.get("/courses/")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_instructor_can_create_course(self):
        """Test that instructors can create courses."""
        self.client.force_authenticate(user=self.instructor)

        response = self.client.post("/courses/", {
            "title": "New Course",
            "description": "Course description",
        })

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["title"], "New Course")
        self.assertFalse(response.data["is_published"])  # Draft by default

    def test_student_cannot_create_course(self):
        """Test that students cannot create courses."""
        self.client.force_authenticate(user=self.student)

        response = self.client.post("/courses/", {
            "title": "New Course",
            "description": "Course description",
        })

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_instructor_sees_own_courses(self):
        """Test that instructors see only their own courses."""
        Course.objects.create(instructor=self.instructor, title="My Course")
        Course.objects.create(instructor=self.other_instructor, title="Other Course")

        self.client.force_authenticate(user=self.instructor)
        response = self.client.get("/courses/")

        self.assertEqual(len(response.data["results"]), 1)
        self.assertEqual(response.data["results"][0]["title"], "My Course")

    def test_student_sees_only_published_courses(self):
        """Test that students see only published courses."""
        Course.objects.create(instructor=self.instructor, title="Draft", is_published=False)
        Course.objects.create(instructor=self.instructor, title="Published", is_published=True)

        self.client.force_authenticate(user=self.student)
        response = self.client.get("/courses/")

        self.assertEqual(len(response.data["results"]), 1)
        self.assertEqual(response.data["results"][0]["title"], "Published")

    def test_instructor_can_update_own_course(self):
        """Test that instructors can update their own courses."""
        course = Course.objects.create(instructor=self.instructor, title="Old Title")

        self.client.force_authenticate(user=self.instructor)
        response = self.client.patch(f"/courses/{course.id}/", {"title": "New Title"})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        course.refresh_from_db()
        self.assertEqual(course.title, "New Title")

    def test_instructor_cannot_update_others_course(self):
        """Test that instructors cannot update other's courses."""
        course = Course.objects.create(instructor=self.other_instructor, title="Other Course")

        self.client.force_authenticate(user=self.instructor)
        response = self.client.patch(f"/courses/{course.id}/", {"title": "Hacked"})

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)


# =============================================================================
# API TESTS - LESSONS
# =============================================================================


class LessonAPITests(APITestCase):
    """Tests for Lesson API endpoints."""

    def setUp(self):
        self.instructor = UserFactory.create_instructor()
        self.student = UserFactory.create_student()
        self.course = Course.objects.create(
            instructor=self.instructor,
            title="Test Course",
            is_published=True,
        )
        self.client = APIClient()

    def test_instructor_can_create_lesson(self):
        """Test that course instructor can create lessons."""
        self.client.force_authenticate(user=self.instructor)

        response = self.client.post(f"/courses/{self.course.id}/lessons/", {
            "title": "New Lesson",
            "content": "Lesson content",
            "order": 1,
        })

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_student_cannot_create_lesson(self):
        """Test that students cannot create lessons."""
        self.client.force_authenticate(user=self.student)

        response = self.client.post(f"/courses/{self.course.id}/lessons/", {
            "title": "New Lesson",
            "content": "Lesson content",
            "order": 1,
        })

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_lessons_returned_in_order(self):
        """Test that lessons are returned in correct order."""
        Lesson.objects.create(course=self.course, title="Third", content="C", order=3)
        Lesson.objects.create(course=self.course, title="First", content="A", order=1)
        Lesson.objects.create(course=self.course, title="Second", content="B", order=2)

        self.client.force_authenticate(user=self.student)
        response = self.client.get(f"/courses/{self.course.id}/lessons/")

        lessons = response.data["results"]
        self.assertEqual(lessons[0]["order"], 1)
        self.assertEqual(lessons[1]["order"], 2)
        self.assertEqual(lessons[2]["order"], 3)


# =============================================================================
# API TESTS - ENROLLMENT
# =============================================================================


class EnrollmentAPITests(APITestCase):
    """Tests for Enrollment API endpoints."""

    def setUp(self):
        self.instructor = UserFactory.create_instructor()
        self.student = UserFactory.create_student()
        self.course = Course.objects.create(
            instructor=self.instructor,
            title="Published Course",
            is_published=True,
        )
        self.draft_course = Course.objects.create(
            instructor=self.instructor,
            title="Draft Course",
            is_published=False,
        )
        self.client = APIClient()

    def test_student_can_enroll_in_published_course(self):
        """Test that students can enroll in published courses."""
        self.client.force_authenticate(user=self.student)

        response = self.client.post("/enrollments/", {"course": self.course.id})

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(Enrollment.objects.filter(
            student=self.student, course=self.course
        ).exists())

    def test_student_cannot_enroll_in_unpublished_course(self):
        """Test that students cannot enroll in unpublished courses."""
        self.client.force_authenticate(user=self.student)

        response = self.client.post("/enrollments/", {"course": self.draft_course.id})

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("unpublished", str(response.data).lower())

    def test_duplicate_enrollment_rejected(self):
        """Test that duplicate enrollments are rejected."""
        Enrollment.objects.create(student=self.student, course=self.course)

        self.client.force_authenticate(user=self.student)
        response = self.client.post("/enrollments/", {"course": self.course.id})

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("already enrolled", str(response.data).lower())

    def test_instructor_cannot_enroll_in_own_course(self):
        """Test that instructors cannot enroll in their own courses."""
        # Create a student role for instructor to test
        instructor_as_student = User.objects.create_user(
            username="instructor_student",
            email="instructor_student@test.com",
            password="testpass123",
            role=User.Role.STUDENT,
        )

        self.client.force_authenticate(user=self.instructor)
        response = self.client.post("/enrollments/", {"course": self.course.id})

        # Instructor role cannot enroll (IsStudent permission)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_instructor_role_cannot_enroll(self):
        """Test that users with instructor role cannot enroll."""
        self.client.force_authenticate(user=self.instructor)

        response = self.client.post("/enrollments/", {"course": self.course.id})

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)


# =============================================================================
# API TESTS - LESSON COMPLETION & PROGRESS
# =============================================================================


class LessonCompletionAPITests(APITestCase):
    """Tests for lesson completion and progress tracking."""

    def setUp(self):
        self.instructor = UserFactory.create_instructor()
        self.student = UserFactory.create_student()
        self.course = Course.objects.create(
            instructor=self.instructor,
            title="Test Course",
            is_published=True,
        )
        self.lesson1 = Lesson.objects.create(
            course=self.course, title="Lesson 1", content="A", order=1
        )
        self.lesson2 = Lesson.objects.create(
            course=self.course, title="Lesson 2", content="B", order=2
        )
        self.enrollment = Enrollment.objects.create(
            student=self.student, course=self.course
        )
        self.client = APIClient()

    def test_student_can_complete_lesson(self):
        """Test that students can mark lessons as complete."""
        self.client.force_authenticate(user=self.student)

        response = self.client.post(
            f"/enrollments/{self.enrollment.id}/complete-lesson/",
            {"lesson_id": self.lesson1.id},
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(LessonCompletion.objects.filter(
            enrollment=self.enrollment, lesson=self.lesson1
        ).exists())

    def test_duplicate_lesson_completion_rejected(self):
        """Test that duplicate lesson completions are rejected."""
        LessonCompletion.objects.create(enrollment=self.enrollment, lesson=self.lesson1)

        self.client.force_authenticate(user=self.student)
        response = self.client.post(
            f"/enrollments/{self.enrollment.id}/complete-lesson/",
            {"lesson_id": self.lesson1.id},
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("already completed", str(response.data).lower())

    def test_cannot_complete_lesson_from_other_course(self):
        """Test that students cannot complete lessons from other courses."""
        other_course = Course.objects.create(
            instructor=self.instructor, title="Other", is_published=True
        )
        other_lesson = Lesson.objects.create(
            course=other_course, title="Other Lesson", content="X", order=1
        )

        self.client.force_authenticate(user=self.student)
        response = self.client.post(
            f"/enrollments/{self.enrollment.id}/complete-lesson/",
            {"lesson_id": other_lesson.id},
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("not found", str(response.data).lower())

    def test_progress_tracking(self):
        """Test progress information is accurate."""
        self.client.force_authenticate(user=self.student)

        # Complete first lesson
        self.client.post(
            f"/enrollments/{self.enrollment.id}/complete-lesson/",
            {"lesson_id": self.lesson1.id},
        )

        response = self.client.get(f"/enrollments/{self.enrollment.id}/progress/")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["total_lessons"], 2)
        self.assertEqual(response.data["completed_lessons"], 1)
        self.assertEqual(response.data["completion_percentage"], 50.0)
        self.assertFalse(response.data["is_completed"])

    @patch("courses.tasks.process_course_completion.delay")
    def test_course_completion_triggers_async_task(self, mock_task):
        """Test that completing all lessons triggers the async task."""
        self.client.force_authenticate(user=self.student)

        # Complete all lessons
        self.client.post(
            f"/enrollments/{self.enrollment.id}/complete-lesson/",
            {"lesson_id": self.lesson1.id},
        )
        self.client.post(
            f"/enrollments/{self.enrollment.id}/complete-lesson/",
            {"lesson_id": self.lesson2.id},
        )

        # Verify task was called
        mock_task.assert_called_once_with(self.enrollment.id)

        # Verify enrollment is marked complete
        self.enrollment.refresh_from_db()
        self.assertTrue(self.enrollment.is_completed)
        self.assertIsNotNone(self.enrollment.completed_at)

    def test_cannot_complete_lesson_after_course_completed(self):
        """Test that lessons cannot be completed after course is done."""
        self.enrollment.is_completed = True
        self.enrollment.completed_at = timezone.now()
        self.enrollment.save()

        self.client.force_authenticate(user=self.student)
        response = self.client.post(
            f"/enrollments/{self.enrollment.id}/complete-lesson/",
            {"lesson_id": self.lesson1.id},
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("already completed", str(response.data).lower())


# =============================================================================
# ASYNC TASK TESTS
# =============================================================================


class CeleryTaskTests(TestCase):
    """Tests for Celery async tasks."""

    def setUp(self):
        self.instructor = UserFactory.create_instructor()
        self.student = UserFactory.create_student()
        self.course = Course.objects.create(
            instructor=self.instructor,
            title="Test Course",
            is_published=True,
        )
        self.enrollment = Enrollment.objects.create(
            student=self.student,
            course=self.course,
            is_completed=True,
            completed_at=timezone.now(),
        )

    def test_process_course_completion_task(self):
        """Test that the course completion task works correctly."""
        from courses.tasks import process_course_completion
        from core.models import Notification

        result = process_course_completion(self.enrollment.id)

        # Verify return value
        self.assertEqual(result["status"], "success")
        self.assertEqual(result["enrollment_id"], self.enrollment.id)

        # Verify notifications were created
        student_notification = Notification.objects.filter(
            user=self.student,
            type=Notification.NotificationType.SYSTEM,
        ).first()
        self.assertIsNotNone(student_notification)
        self.assertIn("completed", student_notification.message.lower())

        instructor_notification = Notification.objects.filter(
            user=self.instructor,
            type=Notification.NotificationType.SYSTEM,
        ).first()
        self.assertIsNotNone(instructor_notification)

    def test_task_handles_missing_enrollment(self):
        """Test that task handles missing enrollment gracefully."""
        from courses.tasks import process_course_completion

        with self.assertRaises(Exception):
            process_course_completion(99999)


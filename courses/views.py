"""
API Views for the courses app.

Provides ViewSets for Course, Lesson, Enrollment, and LessonCompletion.
"""

from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db.models import Q

from .models import Course, Lesson, Enrollment, LessonCompletion
from .serializers import (
    CourseSerializer,
    CourseListSerializer,
    LessonSerializer,
    LessonListSerializer,
    EnrollmentSerializer,
    EnrollmentListSerializer,
    LessonCompletionSerializer,
    CompleteLessonSerializer,
)
from .permissions import (
    IsInstructor,
    IsStudent,
    IsInstructorOrReadOnly,
    IsCourseInstructor,
    IsEnrollmentOwner,
    CanViewCourse,
)


class CourseViewSet(viewsets.ModelViewSet):
    """
    ViewSet for Course management.

    - Instructors can create, update, delete their own courses
    - Students can only view published courses
    - List shows published courses for students, all courses for instructors
    """

    permission_classes = [permissions.IsAuthenticated, IsInstructorOrReadOnly]

    def get_queryset(self):
        """Filter courses based on user role."""
        if getattr(self, "swagger_fake_view", False):
            return Course.objects.none()

        user = self.request.user

        if user.role == "INSTRUCTOR":
            # Instructors see their own courses
            return Course.objects.filter(instructor=user)
        else:
            # Students see only published courses
            return Course.objects.filter(is_published=True)

    def get_serializer_class(self):
        if self.action == "list":
            return CourseListSerializer
        return CourseSerializer

    def get_permissions(self):
        if self.action in ["update", "partial_update", "destroy"]:
            return [permissions.IsAuthenticated(), IsCourseInstructor()]
        return super().get_permissions()

    def retrieve(self, request, *args, **kwargs):
        """Retrieve a course with visibility check."""
        instance = self.get_object()

        # Check if user can view this course
        if not instance.is_published and instance.instructor != request.user:
            return Response(
                {"detail": "Course not found."},
                status=status.HTTP_404_NOT_FOUND,
            )

        serializer = self.get_serializer(instance)
        return Response(serializer.data)


class LessonViewSet(viewsets.ModelViewSet):
    """
    ViewSet for Lesson management.

    - Only course instructors can create/update/delete lessons
    - Lessons are nested under courses
    """

    serializer_class = LessonSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        """Filter lessons by course."""
        if getattr(self, "swagger_fake_view", False):
            return Lesson.objects.none()

        course_id = self.kwargs.get("course_pk")
        return Lesson.objects.filter(course_id=course_id).order_by("order")

    def get_permissions(self):
        if self.action in ["create", "update", "partial_update", "destroy"]:
            return [permissions.IsAuthenticated(), IsInstructor()]
        return super().get_permissions()

    def create(self, request, *args, **kwargs):
        """Create a lesson for a course."""
        course_id = self.kwargs.get("course_pk")

        try:
            course = Course.objects.get(id=course_id)
        except Course.DoesNotExist:
            return Response(
                {"detail": "Course not found."},
                status=status.HTTP_404_NOT_FOUND,
            )

        # Only course instructor can add lessons
        if course.instructor != request.user:
            return Response(
                {"detail": "You can only add lessons to your own courses."},
                status=status.HTTP_403_FORBIDDEN,
            )

        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save(course=course)

        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def update(self, request, *args, **kwargs):
        """Update a lesson (only by course instructor)."""
        lesson = self.get_object()

        if lesson.course.instructor != request.user:
            return Response(
                {"detail": "You can only edit lessons in your own courses."},
                status=status.HTTP_403_FORBIDDEN,
            )

        return super().update(request, *args, **kwargs)

    def destroy(self, request, *args, **kwargs):
        """Delete a lesson (only by course instructor)."""
        lesson = self.get_object()

        if lesson.course.instructor != request.user:
            return Response(
                {"detail": "You can only delete lessons in your own courses."},
                status=status.HTTP_403_FORBIDDEN,
            )

        return super().destroy(request, *args, **kwargs)


class EnrollmentViewSet(viewsets.ModelViewSet):
    """
    ViewSet for Enrollment management.

    - Students can enroll in published courses
    - Students can view their enrollments and progress
    - Students can mark lessons as complete
    """

    permission_classes = [permissions.IsAuthenticated, IsStudent]
    http_method_names = ["get", "post", "delete"]

    def get_queryset(self):
        """Return enrollments for the current user."""
        if getattr(self, "swagger_fake_view", False):
            return Enrollment.objects.none()

        return Enrollment.objects.filter(
            student=self.request.user
        ).select_related("course", "student")

    def get_serializer_class(self):
        if self.action == "list":
            return EnrollmentListSerializer
        if self.action == "complete_lesson":
            return CompleteLessonSerializer
        return EnrollmentSerializer

    @action(detail=True, methods=["post"], url_path="complete-lesson")
    def complete_lesson(self, request, pk=None):
        """
        Mark a lesson as complete for this enrollment.

        POST /enrollments/{id}/complete-lesson/
        Body: {"lesson_id": 1}
        """
        enrollment = self.get_object()

        # Verify ownership
        if enrollment.student != request.user:
            return Response(
                {"detail": "You can only complete lessons in your own enrollments."},
                status=status.HTTP_403_FORBIDDEN,
            )

        # Check if already completed
        if enrollment.is_completed:
            return Response(
                {"detail": "This course is already completed."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        serializer = CompleteLessonSerializer(
            data=request.data,
            context={"request": request, "enrollment": enrollment},
        )
        serializer.is_valid(raise_exception=True)
        completion = serializer.save()

        # Refresh enrollment to get updated progress
        enrollment.refresh_from_db()

        return Response(
            {
                "detail": "Lesson marked as complete.",
                "lesson_completion": LessonCompletionSerializer(completion).data,
                "progress": {
                    "completed_lessons": enrollment.completed_lessons_count,
                    "total_lessons": enrollment.total_lessons,
                    "completion_percentage": enrollment.completion_percentage,
                    "is_course_completed": enrollment.is_completed,
                },
            },
            status=status.HTTP_201_CREATED,
        )

    @action(detail=True, methods=["get"], url_path="progress")
    def progress(self, request, pk=None):
        """
        Get detailed progress for an enrollment.

        GET /enrollments/{id}/progress/
        """
        enrollment = self.get_object()

        if enrollment.student != request.user:
            return Response(
                {"detail": "You can only view your own progress."},
                status=status.HTTP_403_FORBIDDEN,
            )

        # Get all lessons with completion status
        lessons = enrollment.course.lessons.all().order_by("order")
        completed_lesson_ids = set(
            enrollment.lesson_completions.values_list("lesson_id", flat=True)
        )

        lesson_progress = []
        for lesson in lessons:
            lesson_progress.append({
                "id": lesson.id,
                "title": lesson.title,
                "order": lesson.order,
                "is_completed": lesson.id in completed_lesson_ids,
            })

        return Response({
            "enrollment_id": enrollment.id,
            "course": {
                "id": enrollment.course.id,
                "title": enrollment.course.title,
            },
            "total_lessons": enrollment.total_lessons,
            "completed_lessons": enrollment.completed_lessons_count,
            "completion_percentage": enrollment.completion_percentage,
            "is_completed": enrollment.is_completed,
            "completed_at": enrollment.completed_at,
            "lessons": lesson_progress,
        })


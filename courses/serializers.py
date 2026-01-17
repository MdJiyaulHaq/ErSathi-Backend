"""
Serializers for the courses app.

Handles Course, Lesson, Enrollment, and LessonCompletion models.
"""

from rest_framework import serializers
from django.utils import timezone
from .models import Course, Lesson, Enrollment, LessonCompletion


class LessonSerializer(serializers.ModelSerializer):
    """Serializer for Lesson model."""

    class Meta:
        model = Lesson
        fields = ["id", "title", "content", "order", "created_at"]
        read_only_fields = ["id", "created_at"]


class LessonListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for listing lessons (without full content)."""

    class Meta:
        model = Lesson
        fields = ["id", "title", "order", "created_at"]
        read_only_fields = ["id", "created_at"]


class CourseSerializer(serializers.ModelSerializer):
    """Serializer for Course model with nested lessons."""

    instructor_name = serializers.CharField(
        source="instructor.get_full_name", read_only=True
    )
    instructor_email = serializers.EmailField(
        source="instructor.email", read_only=True
    )
    total_lessons = serializers.IntegerField(read_only=True)
    lessons = LessonListSerializer(many=True, read_only=True)

    class Meta:
        model = Course
        fields = [
            "id",
            "title",
            "description",
            "is_published",
            "instructor",
            "instructor_name",
            "instructor_email",
            "total_lessons",
            "lessons",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "instructor", "created_at", "updated_at"]

    def create(self, validated_data):
        """Set instructor to the current user on creation."""
        validated_data["instructor"] = self.context["request"].user
        return super().create(validated_data)


class CourseListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for listing courses."""

    instructor_name = serializers.CharField(
        source="instructor.get_full_name", read_only=True
    )
    total_lessons = serializers.IntegerField(read_only=True)

    class Meta:
        model = Course
        fields = [
            "id",
            "title",
            "description",
            "is_published",
            "instructor_name",
            "total_lessons",
            "created_at",
        ]


class LessonCompletionSerializer(serializers.ModelSerializer):
    """Serializer for LessonCompletion model."""

    lesson_title = serializers.CharField(source="lesson.title", read_only=True)
    lesson_order = serializers.IntegerField(source="lesson.order", read_only=True)

    class Meta:
        model = LessonCompletion
        fields = ["id", "lesson", "lesson_title", "lesson_order", "completed_at"]
        read_only_fields = ["id", "completed_at"]


class EnrollmentSerializer(serializers.ModelSerializer):
    """Serializer for Enrollment model with progress info."""

    course_title = serializers.CharField(source="course.title", read_only=True)
    student_email = serializers.EmailField(source="student.email", read_only=True)
    total_lessons = serializers.IntegerField(read_only=True)
    completed_lessons_count = serializers.IntegerField(read_only=True)
    completion_percentage = serializers.FloatField(read_only=True)
    lesson_completions = LessonCompletionSerializer(many=True, read_only=True)

    class Meta:
        model = Enrollment
        fields = [
            "id",
            "student",
            "student_email",
            "course",
            "course_title",
            "enrolled_at",
            "is_completed",
            "completed_at",
            "total_lessons",
            "completed_lessons_count",
            "completion_percentage",
            "lesson_completions",
        ]
        read_only_fields = [
            "id",
            "student",
            "enrolled_at",
            "is_completed",
            "completed_at",
        ]

    def validate_course(self, value):
        """Validate course for enrollment."""
        user = self.context["request"].user

        # Course must be published
        if not value.is_published:
            raise serializers.ValidationError(
                "Cannot enroll in an unpublished course."
            )

        # Instructors cannot enroll in their own courses
        if value.instructor == user:
            raise serializers.ValidationError(
                "Instructors cannot enroll in their own courses."
            )

        # Check for duplicate enrollment
        if Enrollment.objects.filter(student=user, course=value).exists():
            raise serializers.ValidationError(
                "You are already enrolled in this course."
            )

        return value

    def create(self, validated_data):
        """Set student to the current user on creation."""
        validated_data["student"] = self.context["request"].user
        return super().create(validated_data)


class EnrollmentListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for listing enrollments."""

    course_title = serializers.CharField(source="course.title", read_only=True)
    completion_percentage = serializers.FloatField(read_only=True)

    class Meta:
        model = Enrollment
        fields = [
            "id",
            "course",
            "course_title",
            "enrolled_at",
            "is_completed",
            "completion_percentage",
        ]


class CompleteLessonSerializer(serializers.Serializer):
    """Serializer for marking a lesson as complete."""

    lesson_id = serializers.IntegerField()

    def validate_lesson_id(self, value):
        """Validate the lesson belongs to the enrolled course."""
        enrollment = self.context.get("enrollment")

        try:
            lesson = Lesson.objects.get(id=value, course=enrollment.course)
        except Lesson.DoesNotExist:
            raise serializers.ValidationError(
                "Lesson not found in this course."
            )

        # Check if already completed
        if LessonCompletion.objects.filter(
            enrollment=enrollment, lesson=lesson
        ).exists():
            raise serializers.ValidationError(
                "This lesson is already completed."
            )

        return value

    def create(self, validated_data):
        """Create lesson completion record."""
        enrollment = self.context["enrollment"]
        lesson = Lesson.objects.get(id=validated_data["lesson_id"])

        completion = LessonCompletion.objects.create(
            enrollment=enrollment,
            lesson=lesson,
        )

        # Check if all lessons are completed
        self._check_course_completion(enrollment)

        return completion

    def _check_course_completion(self, enrollment):
        """Check if course is completed and trigger async task."""
        from .tasks import process_course_completion

        if enrollment.completed_lessons_count >= enrollment.total_lessons:
            if enrollment.total_lessons > 0 and not enrollment.is_completed:
                enrollment.is_completed = True
                enrollment.completed_at = timezone.now()
                enrollment.save()

                # Trigger async task
                process_course_completion.delay(enrollment.id)

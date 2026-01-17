from django.db import models
from django.conf import settings
from django.utils.translation import gettext_lazy as _


class Course(models.Model):
    """
    Course created by an instructor.
    Courses start in draft state (is_published=False) and must be published
    to be visible to students.
    """

    instructor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="courses_created",
        limit_choices_to={"role": "INSTRUCTOR"},
    )
    title = models.CharField(_("title"), max_length=255)
    description = models.TextField(_("description"), blank=True)
    is_published = models.BooleanField(
        _("published"),
        default=False,
        help_text=_("Only published courses are visible to students."),
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _("course")
        verbose_name_plural = _("courses")
        ordering = ["-created_at"]

    def __str__(self):
        status = "Published" if self.is_published else "Draft"
        return f"{self.title} [{status}]"

    @property
    def total_lessons(self):
        return self.lessons.count()


class Lesson(models.Model):
    """
    Ordered lesson within a course.
    Lessons are managed by the course instructor and immutable to students.
    """

    course = models.ForeignKey(
        Course,
        on_delete=models.CASCADE,
        related_name="lessons",
    )
    title = models.CharField(_("title"), max_length=255)
    content = models.TextField(_("content"), help_text=_("Lesson content (plain text)."))
    order = models.PositiveIntegerField(
        _("order"),
        help_text=_("Order index for lesson sequencing."),
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = _("lesson")
        verbose_name_plural = _("lessons")
        ordering = ["course", "order"]
        unique_together = ["course", "order"]

    def __str__(self):
        return f"{self.course.title} - Lesson {self.order}: {self.title}"


class Enrollment(models.Model):
    """
    Student enrollment in a course.
    - Students can only enroll in published courses
    - Students cannot enroll in the same course twice
    - Instructors cannot enroll in their own courses
    """

    student = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="enrollments",
        limit_choices_to={"role": "STUDENT"},
    )
    course = models.ForeignKey(
        Course,
        on_delete=models.CASCADE,
        related_name="enrollments",
    )
    enrolled_at = models.DateTimeField(auto_now_add=True)
    is_completed = models.BooleanField(default=False)
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name = _("enrollment")
        verbose_name_plural = _("enrollments")
        ordering = ["-enrolled_at"]
        unique_together = ["student", "course"]

    def __str__(self):
        status = "Completed" if self.is_completed else "In Progress"
        return f"{self.student.email} - {self.course.title} [{status}]"

    @property
    def completed_lessons_count(self):
        return self.lesson_completions.count()

    @property
    def total_lessons(self):
        return self.course.total_lessons

    @property
    def completion_percentage(self):
        total = self.total_lessons
        if total == 0:
            return 0
        return round((self.completed_lessons_count / total) * 100, 2)


class LessonCompletion(models.Model):
    """
    Tracks individual lesson completions by a student.
    When all lessons are completed, the enrollment is marked complete
    and an async task is triggered.
    """

    enrollment = models.ForeignKey(
        Enrollment,
        on_delete=models.CASCADE,
        related_name="lesson_completions",
    )
    lesson = models.ForeignKey(
        Lesson,
        on_delete=models.CASCADE,
        related_name="completions",
    )
    completed_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = _("lesson completion")
        verbose_name_plural = _("lesson completions")
        ordering = ["-completed_at"]
        unique_together = ["enrollment", "lesson"]

    def __str__(self):
        return f"{self.enrollment.student.email} completed {self.lesson.title}"

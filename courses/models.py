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

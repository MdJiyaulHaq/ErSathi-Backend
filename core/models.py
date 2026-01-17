from django.contrib.auth.models import AbstractUser
from django.db import models
from django.contrib import admin
from django.core.validators import RegexValidator, MinLengthValidator
from django.utils.translation import gettext_lazy as _
from django.conf import settings

from disciplines.models import Discipline

# core models


class User(AbstractUser):
    class Role(models.TextChoices):
        STUDENT = "STUDENT", _("Student")
        INSTRUCTOR = "INSTRUCTOR", _("Instructor")

    username = models.CharField(
        _("username"),
        max_length=150,
        unique=True,
        help_text=_(
            "Required. 150 characters or fewer. Letters, digits and @/./+/-/_ only."
        ),
        validators=[AbstractUser.username_validator],
        error_messages={
            "unique": _("A user with that username already exists."),
        },
    )
    email = models.EmailField(_("email address"), unique=True)
    role = models.CharField(
        _("role"),
        max_length=20,
        choices=Role.choices,
        default=Role.STUDENT,
        help_text=_("User role: Student or Instructor"),
    )
    date_joined = models.DateTimeField(auto_now_add=True)
    modified_at = models.DateTimeField(auto_now=True)
    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["username"]

    class Meta:
        verbose_name = _("user")
        verbose_name_plural = _("users")
        ordering = ["-date_joined"]

    @property
    def is_student(self):
        return self.role == self.Role.STUDENT

    @property
    def is_instructor(self):
        return self.role == self.Role.INSTRUCTOR

    def __str__(self):
        return f"{self.get_full_name()} ({self.email})"


class StudentProfile(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="student_profile",
    )
    first_name = models.CharField(max_length=55, default="")
    last_name = models.CharField(max_length=55, default="")
    university = models.CharField(max_length=255, default="")
    program = models.ForeignKey(
        Discipline,
        on_delete=models.PROTECT,
        related_name="students",
    )

    phone = models.CharField(
        max_length=20,
        validators=[
            RegexValidator(
                regex=r"^(?:\+977|00977)?(?:98|97)\d{8}$",
                message="Phone number must start with '+977' or '00977' followed by a 10-digit number starting with 98 or 97.",
            ),
            MinLengthValidator(9),
        ],
        blank=True,
    )
    date_of_birth = models.DateField(
        _("date of birth"),
        blank=True,
        null=True,
        help_text=_("Format: YYYY-MM-DD"),
    )
    bio = models.TextField(blank=True)
    registration_date = models.DateTimeField(auto_now_add=True)
    last_active = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _("student profile")
        verbose_name_plural = _("student profiles")


class Notification(models.Model):
    class NotificationType(models.TextChoices):
        EXAM = "EXAM", "Exam"
        MATERIAL = "STUDY_MATERIAL", "Study Material"
        SYSTEM = "SYSTEM", "System"
        ANNOUNCEMENT = "ANNOUNCEMENT", "Announcement"

    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="notifications"
    )
    type = models.CharField(
        max_length=20, choices=NotificationType.choices, default=NotificationType.SYSTEM
    )
    message = models.TextField()
    link = models.URLField(blank=True, null=True)
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    read_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.user.email} | {self.message[:30]}{'...' if len(self.message) > 30 else ''}"

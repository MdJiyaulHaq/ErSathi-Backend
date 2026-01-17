from django.contrib import admin
from .models import Course, Lesson, Enrollment, LessonCompletion


class LessonInline(admin.TabularInline):
    model = Lesson
    extra = 1
    ordering = ["order"]


class LessonCompletionInline(admin.TabularInline):
    model = LessonCompletion
    extra = 0
    readonly_fields = ("lesson", "completed_at")
    can_delete = False


@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    list_display = ("title", "instructor", "is_published", "total_lessons", "created_at")
    list_filter = ("is_published", "created_at")
    search_fields = ("title", "description", "instructor__email")
    readonly_fields = ("created_at", "updated_at")
    inlines = [LessonInline]

    def total_lessons(self, obj):
        return obj.lessons.count()
    total_lessons.short_description = "Lessons"


@admin.register(Lesson)
class LessonAdmin(admin.ModelAdmin):
    list_display = ("title", "course", "order", "created_at")
    list_filter = ("course",)
    search_fields = ("title", "content")
    ordering = ["course", "order"]


@admin.register(Enrollment)
class EnrollmentAdmin(admin.ModelAdmin):
    list_display = ("student", "course", "is_completed", "completion_percentage", "enrolled_at")
    list_filter = ("is_completed", "course", "enrolled_at")
    search_fields = ("student__email", "course__title")
    readonly_fields = ("enrolled_at", "completed_at", "completion_percentage")
    inlines = [LessonCompletionInline]

    def completion_percentage(self, obj):
        return f"{obj.completion_percentage}%"
    completion_percentage.short_description = "Progress"


@admin.register(LessonCompletion)
class LessonCompletionAdmin(admin.ModelAdmin):
    list_display = ("enrollment", "lesson", "completed_at")
    list_filter = ("completed_at",)
    search_fields = ("enrollment__student__email", "lesson__title")

from django.contrib import admin
from .models import Course, Lesson


class LessonInline(admin.TabularInline):
    model = Lesson
    extra = 1
    ordering = ["order"]


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

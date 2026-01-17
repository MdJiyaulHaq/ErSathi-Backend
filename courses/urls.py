"""
URL configuration for the courses app.

Provides REST API endpoints for:
- Courses: /courses/
- Lessons: /courses/{id}/lessons/
- Enrollments: /enrollments/
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework_nested import routers

from .views import CourseViewSet, LessonViewSet, EnrollmentViewSet

# Main router for courses and enrollments
router = DefaultRouter()
router.register(r"courses", CourseViewSet, basename="course")
router.register(r"enrollments", EnrollmentViewSet, basename="enrollment")

# Nested router for lessons under courses
courses_router = routers.NestedDefaultRouter(router, r"courses", lookup="course")
courses_router.register(r"lessons", LessonViewSet, basename="course-lessons")

urlpatterns = [
    path("", include(router.urls)),
    path("", include(courses_router.urls)),
]

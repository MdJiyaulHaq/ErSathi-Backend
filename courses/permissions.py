"""
Custom permissions for the courses app.

These permissions enforce role-based access control for courses,
lessons, enrollments, and lesson completions.
"""

from rest_framework import permissions


class IsInstructor(permissions.BasePermission):
    """
    Permission that only allows instructors to access.
    """

    message = "Only instructors can perform this action."

    def has_permission(self, request, view):
        return (
            request.user.is_authenticated
            and request.user.role == "INSTRUCTOR"
        )


class IsStudent(permissions.BasePermission):
    """
    Permission that only allows students to access.
    """

    message = "Only students can perform this action."

    def has_permission(self, request, view):
        return (
            request.user.is_authenticated
            and request.user.role == "STUDENT"
        )


class IsInstructorOrReadOnly(permissions.BasePermission):
    """
    Permission that allows instructors full access,
    but only read access for others.
    """

    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return request.user.is_authenticated
        return (
            request.user.is_authenticated
            and request.user.role == "INSTRUCTOR"
        )


class IsCourseInstructor(permissions.BasePermission):
    """
    Object-level permission that only allows the course instructor
    to modify the course or its lessons.
    """

    message = "You can only manage your own courses."

    def has_object_permission(self, request, view, obj):
        # Read permissions for authenticated users
        if request.method in permissions.SAFE_METHODS:
            return True

        # Write permissions only for the course instructor
        if hasattr(obj, "instructor"):
            return obj.instructor == request.user
        elif hasattr(obj, "course"):
            return obj.course.instructor == request.user

        return False


class IsEnrollmentOwner(permissions.BasePermission):
    """
    Object-level permission that only allows the enrolled student
    to view or interact with their enrollment.
    """

    message = "You can only access your own enrollments."

    def has_object_permission(self, request, view, obj):
        return obj.student == request.user


class CanViewCourse(permissions.BasePermission):
    """
    Permission to view a course.
    - Instructors can view their own courses (published or draft)
    - Students can only view published courses
    """

    def has_object_permission(self, request, view, obj):
        user = request.user

        # Instructor can always view their own courses
        if obj.instructor == user:
            return True

        # Others can only view published courses
        return obj.is_published

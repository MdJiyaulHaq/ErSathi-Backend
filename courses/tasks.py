"""
Celery tasks for the courses app.

These tasks run asynchronously outside the request/response cycle.
"""

import logging
from celery import shared_task
from django.utils import timezone

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=3)
def process_course_completion(self, enrollment_id: int):
    """
    Process course completion asynchronously.

    This task is triggered when a student completes all lessons in a course.
    It demonstrates proper async processing outside the request/response cycle.

    Actions performed:
    1. Log the completion event
    2. Create a completion summary record
    3. Could send notification (simulated with logging)

    Args:
        enrollment_id: The ID of the completed enrollment
    """
    from .models import Enrollment
    from core.models import Notification

    try:
        enrollment = Enrollment.objects.select_related(
            "student", "course", "course__instructor"
        ).get(id=enrollment_id)

        # Log completion for analytics
        logger.info(
            f"Course completion processed: "
            f"Student={enrollment.student.email}, "
            f"Course={enrollment.course.title}, "
            f"Completed at={enrollment.completed_at}"
        )

        # Create notification for the student
        Notification.objects.create(
            user=enrollment.student,
            type=Notification.NotificationType.SYSTEM,
            message=f"Congratulations! You have completed the course: {enrollment.course.title}",
            is_read=False,
        )

        # Create notification for the instructor
        Notification.objects.create(
            user=enrollment.course.instructor,
            type=Notification.NotificationType.SYSTEM,
            message=f"Student {enrollment.student.get_full_name()} has completed your course: {enrollment.course.title}",
            is_read=False,
        )

        logger.info(f"Notifications created for enrollment {enrollment_id}")

        return {
            "status": "success",
            "enrollment_id": enrollment_id,
            "student": enrollment.student.email,
            "course": enrollment.course.title,
            "completed_at": str(enrollment.completed_at),
        }

    except Enrollment.DoesNotExist:
        logger.error(f"Enrollment {enrollment_id} not found")
        raise
    except Exception as exc:
        logger.error(f"Error processing course completion: {exc}")
        # Retry the task with exponential backoff
        raise self.retry(exc=exc, countdown=60 * (2 ** self.request.retries))

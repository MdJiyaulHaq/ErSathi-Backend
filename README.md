# ErSathi Learning Platform

An open source preparation platform built with Django REST API for online learning with course management, student enrollments, and progress tracking.

## Tech Stack

- **Backend:** Django 5.2 + DRF 3.16
- **Database:** PostgreSQL 17
- **Async:** Celery 5.4 + Redis
- **Auth:** JWT (djoser + simplejwt)
- **Docs:** Swagger UI at `/api/docs/`

## Quick Start

```bash
# Clone and configure
git clone https://github.com/MdJiyaulHaq/ersathi-backend.git
cd ersathi-backend
cp .env.example .env  # Edit with your settings

# Switch to new/ole-assignment branch
git checkout new/ole-assignment

# Start all services (web, db, redis, celery)
docker-compose -f docker-compose.local.yml up --build

# Create admin user
docker-compose -f docker-compose.local.yml exec web python manage.py createsuperuser
```

**Access:**
- Admin: http://localhost:8000/admin/
- Docs: http://localhost:8000/api/docs/

## Features

- **Role-based access:** Students and Instructors with distinct permissions
- **Course management:** Draft/published states, ordered lessons
- **Progress tracking:** Lesson completions with percentage calculations
- **Async processing:** Celery tasks triggered on course completion

## API Endpoints

### Authentication
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/auth/users/` | Register |
| POST | `/auth/jwt/create/` | Login |
| POST | `/auth/jwt/refresh/` | Refresh token |

### Courses & Lessons (Instructors)
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/courses/` | Create course |
| PATCH | `/courses/{id}/` | Update course |
| POST | `/courses/{id}/lessons/` | Add lesson |

### Enrollments (Students)
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/courses/` | Browse published courses |
| POST | `/enrollments/` | Enroll in course |
| POST | `/enrollments/{id}/complete-lesson/` | Complete lesson |
| GET | `/enrollments/{id}/progress/` | View progress |

## Testing

```bash
docker-compose -f docker-compose.local.yml exec web python manage.py test courses
```

## Project Structure

```
├── core/           # User model with roles
├── courses/        # Course, Lesson, Enrollment, LessonCompletion
│   ├── models.py
│   ├── views.py
│   ├── serializers.py
│   ├── permissions.py
│   ├── tasks.py    # Celery async tasks
│   └── tests.py
└── erSathi/        # Django settings & Celery config
```

## License

MIT

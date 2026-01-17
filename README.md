# ErSathi Backend

ErSathi is a comprehensive backend system built with Django and Django REST framework, designed to manage educational assessments, user progress tracking, and gamification features. The system provides a robust API for integrating with frontend applications.

## Project Overview

This project provides the following key features:

- User authentication and authorization
- Exam/Assessment management system
- Study materials management
- Progress tracking for students
- Gamification elements (badges and likes)
- Tagging system for organizing content
- Discipline-based content organization
- Question bank management

## Getting Started

To set up the project locally, follow these steps:

1. Clone the repository:

```bash
git clone https://github.com/MdJiyaulHaq/ersathi-backend.git
cd ersathi-backend
```

2. Copy the example environment file and adjust values if needed:

```bash
cp .env.example .env
```

3. Build and start the containers:

```bash
docker-compose -f docker-compose.local.yml up --build
```

The application will be available at `http://localhost:8000`

## Project Structure

The project is organized into several Django apps:

- **core**: Core user models and authentication
- **assessments**: Exam and assessment management
- **disciplines**: Discipline-based content organization
- **gamification**: Badge and achievement system
- **likes**: Voting system for content
- **progress**: Student progress tracking
- **questions**: Question bank management
- **study_materials**: Study materials and resources
- **subjects**: Subject management
- **tags**: Tagging system

## Features

### Users & Authentication

- User registration and login
- Role-based access control
- Student and educator profiles

### Exams & Assessments

- Create and manage exams
- Multiple question types support
- Exam attempts and results tracking

### Study Materials

- Upload and manage study resources
- Organize by subjects and disciplines
- Access control for materials

### Progress Tracking

- Track student progress
- Generate progress reports
- Set learning goals

### Gamification

- Earn badges based on achievements
- Leaderboard system
- Points system

## Live Demo

Live at: [http://150.230.12.113:8000](http://150.230.12.113:8000)
Coming soon: [https://api.ersathi.com](https://api.ersathi.com)

### API Documentation

The API documentation is automatically generated using drf-spectacular and can be accessed at: [http://150.230.12.113:8000/api/docs/](http://150.230.12.113:8000/api/docs/)

## Linting and Running Tests

To run linters and tests, you can use the following commands:

```bash
docker compose run --rm web sh -c "flake8"
docker compose run --rm web sh -c "pytest"
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Open a Pull Request

For major changes or features, please open an issue to discuss your proposal first.

If your contribution requires authentication (e.g., API token), please contact the maintainers to receive a development token for local testing.

## Maintainers

- Md Jiyaul Haq ([https://github.com/MdJiyaulHaq](https://github.com/MdJiyaulHaq))

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.

## Contributors

# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Django-based REST API for managing academic thesis teams, topics, and collaboration between students, supervisors, and dean's office staff. Uses PostgreSQL, Redis, Django Channels for WebSocket communication, JWT authentication, and SendGrid for emails.

## Common Commands

### Development Server
```bash
# Standard Django development server (no WebSocket support)
python manage.py runserver

# Development server with WebSocket support (recommended)
daphne -b 0.0.0.0 -p 8000 DTest.asgi:application
```

### Database Operations
```bash
# Make migrations after model changes
python manage.py makemigrations

# Apply migrations
python manage.py migrate

# Create superuser for admin access
python manage.py createsuperuser
```

### Static Files
```bash
# Collect static files for production
python manage.py collectstatic --noinput
```

### Docker Commands
```bash
# Build Docker image
docker build -t thesis-system .

# Run containerized application
docker run -p 8000:8000 --env-file .env thesis-system
```

## Architecture Overview

### Multi-Role User System
- **CustomUser Model** (`users/models.py`): Custom AbstractBaseUser with role-based system ("Student", "Supervisor", "Dean Office")
- **Auto-Profile Creation**: Profiles automatically created via Django signals (`profiles/models.py:126-135`) when user is created based on role
- **Role-Specific Profiles**: StudentProfile, SupervisorProfile, DeanOfficeProfile with different required fields
- **Profile Completion Tracking**: `is_profile_completed` flag on CustomUser automatically updated when profile fields are filled

### Team Management Flow
1. **Team Creation**: Student creates team linked to a ThesisTopic (one-to-one relationship)
2. **Join Requests**: Students request to join teams via JoinRequest model
3. **Skill Validation**: Teams must have ≥4 matching skills from topic's required skills (`teams/models.py:34-38`)
4. **Supervisor Assignment**: Teams request supervisors via SupervisorRequest model
5. **Approval Workflow**: pending → approved → team_approved
6. **Supervisor Limits**: Max 10 teams per supervisor (enforced in `teams/models.py:48`)

### WebSocket Architecture
- **ASGI Configuration** (`DTest/asgi.py`): ProtocolTypeRouter routes HTTP and WebSocket connections
- **JWT WebSocket Auth** (`notifications/middleware.py`): JWTAuthMiddleware authenticates WebSocket connections via query string token (`?token=<jwt>`)
- **WebSocket Routes** (`DTest/routing.py`):
  - `/ws/notifications/` - Real-time notifications
  - `/ws/chat/<chat_id>/` - Real-time chat rooms
- **Consumers**: ChatConsumer and NotificationConsumer handle WebSocket events

### Authentication & Security
- **JWT Tokens**: Access token (1 hour), refresh token (7 days)
- **Login Protection**: Failed login tracking with temporary blocking (`users/models.py:34-38`)
- **Access Logging**: All login/logout events tracked in AccessLog model
- **Email Verification**: SendGrid integration for user verification

### Database Relationships
- **ThesisTopic ←→ Team**: OneToOne (one topic per team)
- **Team ←→ Students**: ManyToMany through Membership model
- **Team → Supervisor**: ForeignKey (one supervisor per team)
- **StudentProfile/SupervisorProfile → Skills**: ManyToMany (max 5 for students, 10 for supervisors)

## Important Implementation Notes

### When Modifying User/Profile System
- Profiles are auto-created by signals - don't create manually in save() method
- Always update `is_profile_completed` when profile fields change
- Use OneToOne with user as primary_key for profile models
- Role validation happens in CustomUser, not in profiles

### When Working with Teams
- Always check `has_required_skills()` before supervisor assignment
- Supervisor team count validation is in `approve_team()` and `approve_by_supervisor_and_send_to_dean()`
- Use Membership model for team-student relationships, not direct ManyToMany
- Team status workflow must be followed: pending → approved → team_approved

### When Adding WebSocket Features
- WebSocket connections require JWT token in query string: `ws://host/path/?token=<jwt>`
- Always use JWTAuthMiddleware wrapper in routing configuration
- Call `django.setup()` before importing routing in asgi.py
- Use channels-redis for production (currently InMemoryChannelLayer in settings)

### When Modifying Settings
- Environment variables loaded via python-decouple and python-dotenv
- Required env vars: DATABASE_URL, SECRET_KEY, SENDGRID_API_KEY, REDIS_URL
- CORS origins dynamically built from FRONTEND_URL and BACKEND_URL
- Channel layers use InMemoryChannelLayer (development only)

## API Structure

- `/api/users/` - Authentication endpoints (register, login, token refresh)
- `/api/profiles/` - Profile management (student, supervisor, dean-office)
- `/api/topics/` - Thesis topic CRUD
- `/api/teams/` - Team management, join requests, supervisor requests, likes
- `/api/notifications/` - Notification list and mark-as-read
- `/api/chat/` - Chat rooms and message history
- `/swagger/` - Interactive API documentation
- `/redoc/` - ReDoc API documentation

## Testing Considerations

- Use `python manage.py test <app_name>` to run tests for specific app
- WebSocket tests require Daphne server running
- Authentication tests should verify failed login blocking mechanism
- Team tests must validate skill requirements and supervisor limits
- Profile tests should verify auto-creation via signals

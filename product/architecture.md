
## Tech Stack
- **Frontend**: React.js with TypeScript
- **Backend**: FastAPI (Python)
- **Database**: PostgreSQL
- **Authentication**: JWT tokens
- **Email**: SMTP service for reminders

## Database Schema

### Core Tables

```
┌─────────────────────────┐    ┌─────────────────────────┐    ┌─────────────────────────┐
│        users            │    │      workspaces         │    │        pages            │
├─────────────────────────┤    ├─────────────────────────┤    ├─────────────────────────┤
│ id (PK)          UUID   │    │ id (PK)          UUID   │    │ id (PK)          UUID   │
│ email            VARCHAR│    │ name             VARCHAR│    │ title            VARCHAR│
│ password_hash    VARCHAR│    │ description      TEXT   │    │ content          JSONB  │
│ name             VARCHAR│    │ owner_id (FK)    UUID   │────│ workspace_id(FK) UUID   │
│ created_at       TIMESTAMP   │ created_at       TIMESTAMP   │ parent_id (FK)   UUID   │
│ updated_at       TIMESTAMP   │ updated_at       TIMESTAMP   │ created_by (FK)  UUID   │
└─────────────────────────┘    └─────────────────────────┘    │ created_at       TIMESTAMP
                                                              │ updated_at       TIMESTAMP
                                                              └─────────────────────────┘
```

### Collaboration Tables

```
┌─────────────────────────┐    ┌─────────────────────────┐    ┌─────────────────────────┐
│   workspace_members     │    │       comments          │    │     permissions         │
├─────────────────────────┤    ├─────────────────────────┤    ├─────────────────────────┤
│ id (PK)          UUID   │    │ id (PK)          UUID   │    │ id (PK)          UUID   │
│ workspace_id(FK) UUID   │    │ content          TEXT   │    │ user_id (FK)     UUID   │
│ user_id (FK)     UUID   │    │ page_id (FK)     UUID   │    │ workspace_id(FK) UUID   │
│ role             VARCHAR│    │ user_id (FK)     UUID   │    │ page_id (FK)     UUID   │
│ joined_at        TIMESTAMP   │ created_at       TIMESTAMP   │ permission_type  VARCHAR│
└─────────────────────────┘    │ updated_at       TIMESTAMP   │ granted_at       TIMESTAMP
                               └─────────────────────────┘    └─────────────────────────┘
```

### Task Management Tables

```
┌─────────────────────────┐    ┌─────────────────────────┐
│        tasks            │    │   task_assignments      │
├─────────────────────────┤    ├─────────────────────────┤
│ id (PK)          UUID   │    │ id (PK)          UUID   │
│ title            VARCHAR│    │ task_id (FK)     UUID   │
│ description      TEXT   │    │ user_id (FK)     UUID   │
│ status           VARCHAR│    │ assigned_by (FK) UUID   │
│ priority         VARCHAR│    │ assigned_at      TIMESTAMP
│ due_date         DATE   │    └─────────────────────────┘
│ page_id (FK)     UUID   │
│ created_by (FK)  UUID   │
│ created_at       TIMESTAMP
│ updated_at       TIMESTAMP
└─────────────────────────┘
```

### Activity Logs Table

```
┌─────────────────────────┐
│     activity_logs       │
├─────────────────────────┤
│ id (PK)          UUID   │
│ user_id (FK)     UUID   │
│ workspace_id(FK) UUID   │
│ action_type      VARCHAR│
│ entity_type      VARCHAR│
│ entity_id        UUID   │
│ details          JSONB  │
│ created_at       TIMESTAMP
└─────────────────────────┘
```

## Foreign Key Relationships

```
users (1) ──────────── (*) workspaces (owner_id)
users (1) ──────────── (*) workspace_members (user_id)
users (1) ──────────── (*) pages (created_by)
users (1) ──────────── (*) tasks (created_by)
users (1) ──────────── (*) comments (user_id)
users (1) ──────────── (*) permissions (user_id)

workspaces (1) ─────── (*) pages (workspace_id)
workspaces (1) ─────── (*) workspace_members (workspace_id)
workspaces (1) ─────── (*) permissions (workspace_id)

pages (1) ──────────── (*) pages (parent_id) [self-referencing]
pages (1) ──────────── (*) tasks (page_id)
pages (1) ──────────── (*) comments (page_id)
pages (1) ──────────── (*) permissions (page_id)

tasks (1) ──────────── (*) task_assignments (task_id)
```

## API Architecture

### FastAPI Structure
```
/api/v1/
├── auth/          # Authentication endpoints
├── workspaces/    # Workspace CRUD
├── pages/         # Page management
├── tasks/         # Task operations
├── comments/      # Comment system
├── search/        # Full-text search
└── reminders/     # Email reminder system
```

### Key Features Implementation

**Real-time Collaboration**
- WebSocket connections for live editing
- Operational Transform for conflict resolution
- Presence indicators for active users

**Smart Email Reminders**
- Background task scheduler (Celery/APScheduler) calls API endpoints
- Email service queries `/api/v1/tasks/due-soon` and `/api/v1/tasks/overdue`
- Always uses fresh data, no separate reminder storage needed

**Multi-workspace Support**
- Workspace-scoped queries
- Context switching via workspace_id
- Cross-workspace search with proper permissions

# Backend Interview 02 - FastAPI Events API

A simplified FastAPI-based interview project for managing events with CRUD operations. This project follows a clean architecture pattern with repository-based data access and query separation, but without the complexity of command handlers and message buses.

## 🚀 Features

- **FastAPI** with async/await support
- **PostgreSQL** database with SQLAlchemy ORM
- **Alembic** database migrations
- **Docker Compose** for easy local development
- **Rate limiting** with slowapi
- **CORS** support for frontend integration
- **Pydantic** models for request/response validation
- **Soft delete** pattern for data safety

## 🏗️ Architecture

This project uses a simplified CQRS-like pattern:
- **Repository Pattern**: For create, update, delete operations
- **Query Pattern**: For all read operations  
- **Separation of Concerns**: Clear separation between inputs, outputs, and business logic
- **No Command Handlers**: Direct repository/query usage in views for simplicity

## 📋 Prerequisites

- **Docker & Docker Compose**

## 🔧 Installation & Setup

### 1. Clone the Repository
```bash
git clone <repository-url>
cd backend_interview_02
```

### 2. Start the Application (Docker Compose - Recommended)
```bash
# Start all services (database + API)
docker-compose up -d --build

# The API will be available at http://localhost:8160
```

That's it! Docker Compose handles everything including:
- PostgreSQL database setup
- Python environment and dependencies
- Database migrations
- FastAPI server startup

### Alternative: Local Development Setup
*Only needed if you want to run the API locally outside Docker*

#### Prerequisites for Local Development
- **Python 3.10+**

#### Setup Steps
```bash
# 1. Set up Python Virtual Environment
python -m venv venv

# Activate virtual environment
# On macOS/Linux:
source venv/bin/activate
# On Windows:
# venv\Scripts\activate

# Install Python dependencies
pip install -r requirements.txt

# 2. Environment Configuration
cp .env.local .env

# 3. Start Database Only
docker-compose up -d interview-db

# 4. Run Database Migrations
alembic upgrade head

# 5. Start the API Server
uvicorn main:app --host 0.0.0.0 --port 8600 --reload
```

## 📋 Interview Tasks (Todo)

Here are the tasks to implement:

### 🟢 Task 1: Create Tickets Package Structure
**Goal**: Create a new tickets package
- Create a new `tickets/` directory in the project root

### 🟢 Task 2: Implement TicketType ORM Model
**Goal**: Create the TicketType model with all required fields and business logic.

Create the `TicketType` model in `tickets/orm.py` with the following specifications:

**Model Fields:**
- `id`: Primary key (use UUID similar to Event model)
- `name`: String field (255 chars max)  
- `price`: Decimal field for ticket price
- `description`: Text description field
- `max_quantity`: Optional integer for maximum tickets (nullable, default None)
- `sale_start_date`: Optional timestamp when sales begin (nullable)
- `sale_end_date`: Optional timestamp when sales end (nullable)
- `is_hidden`: Boolean flag to hide from listings (default False)
- `is_waitlistable`: Boolean flag for waitlist capability (default False)
- `event_id`: Foreign key to Event model
- `is_active`: Boolean field for soft deletes (default True)
- `created_at`: DateTime field (auto-generated)
- `updated_at`: DateTime field (auto-updated)

**Relationships:**
- `event`: Many-to-one relationship with Event model
- `tickets`: One-to-many relationship with Ticket model (to be created in next task)

**Class Methods:**
- `get_by_event_id(event_id, db)`: Async method to fetch all ticket types for an event
- `bulk_get(ids, db)`: Async method to fetch multiple ticket types by IDs
- `__repr__`: String representation showing ticket type name

### 🟢 Task 3: Implement Ticket ORM Model  
**Goal**: Create the Ticket model with user assignment and check-in functionality.

Create the `Ticket` model in `tickets/orm.py` with the following specifications:

**Model Fields:**
- `id`: Primary key (UUID)
- `user_id`: String field for user identification (nullable, indexed)
- `event_id`: Foreign key to Event model (indexed)
- `ticket_type_id`: Foreign key to TicketType model
- `is_checked_in`: Boolean flag for event check-in (default False)
- `is_active`: Boolean field for soft deletes (default True)
- `created_at`: DateTime field (auto-generated)
- `updated_at`: DateTime field (auto-updated)

**Relationships:**
- `event`: Many-to-one relationship with Event model
- `ticket_type`: Many-to-one relationship with TicketType model

**Business Logic:**
- Add appropriate indexes for performance
- Include proper foreign key constraints
- Add `__repr__` method for debugging

### 🟢 Task 4: Create CRUD Operations
**Goal**: Implement CRUD operations for ticket models following the existing project structure.
- Follow the same patterns used in the events package

### 🟡 Task 5: Redis Event Caching
**Goal**: Cache events in Redis when they are created.
- Add Redis caching logic to event creation workflow
- Cache event data with appropriate expiration

### 🟡 Task 6: Cache-Enabled Event Reads
**Goal**: Update read operations to use cache for events.
- Modify event queries to check Redis cache first
- Implement cache fallback to database when cache miss occurs
- Add cache warming strategies for frequently accessed events

### 🟢 Task 7: Event Count Endpoint
**Goal**: Add a simple endpoint to get the total count of active events.
- Create `GET /events/count/` endpoint
- Return JSON: `{"count": 42}`
- Use existing query patterns from the events package

### 🔴 Task 8: Auto-Ticket Creation
**Goal**: Create a background task that generates a ticket for the event creator.
- Use Celery to handle background task processing
- When an event is created, automatically create a ticket for the creator
- Ensure proper error handling and retry logic

### 🔴 Task 9: End-to-End Integration Tests
**Goal**: Install Playwright and create integration tests for all CRUD endpoints.
- Install Playwright for Python
- Create test suite covering all event and ticket CRUD operations
- Test complete workflows including background tasks and caching
- Ensure tests run against the full application stack

## 🐳 Docker Usage

### Full Docker Setup
```bash
# Start all services (database + API)
docker-compose up -d

# View logs
docker-compose logs -f

# Stop services
docker-compose down
```

### Database Only
```bash
# Start only the database
docker-compose up -d interview-db
```

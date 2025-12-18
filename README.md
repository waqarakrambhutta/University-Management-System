# University Management System (UMS)

A robust, role-based University Management System built with Django and Django REST Framework. The system enables Professors to manage courses, enroll students, and submit grades with authorized access and audit logging.

## Features

### 1. Role-Based Access Control (RBAC)

- **Professor**: Can enroll students, submit grades, and view their assigned courses.
- **Admin**: Full access to the system.

### 2. Enrollment Management

- **Strict Capacity Control**: Courses have a seat limit (default: 400).
- **Concurrency Protection**: Uses database locks (`select_for_update`) to prevent race conditions during heavy enrollment traffic.
- **Professor-Only Enrollment**: Only professors (or admins) can enroll students.

### 3. Grading System

- **Inline Grading**: Professors can assign grades directly from the course dashboard.
- **Audit Logging**: Every grade change is tracked. The system records:
  - Who made the change.
  - What the previous grade was.
  - What the new grade is.
  - The timestamp of the change.
- **Validations**: Grades are validated to be between 0.00 and 100.00.

### 4. Interactive Frontend

- **Professors Dashboard**: A minimalist, responsive dashboard to view courses.
- **Course Details**: See enrolled students and manage their grades dynamically.
- **Add Students**: Interface to add new student records to the system.

## Setup & Installation

### Prerequisites

- Python 3.10+
- Docker (optional)

### Local Setup

1. **Clone the repository**

   ```bash
   git clone <repository_url>
   cd ums
   ```

2. **Create a Virtual Environment**

   ```bash
   python -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   ```

3. **Install Dependencies**

   ```bash
   pip install -r requirements.txt
   ```

4. **Apply Migrations**

   ```bash
   python manage.py migrate
   ```

5. **Create Superuser**

   ```bash
   python manage.py createsuperuser
   ```

6. **Run Server**
   ```bash
   python manage.py runserver
   ```
   Access the system at `http://localhost:8000/`.

### Docker Setup

1. **Build and Run**
   ```bash
   docker-compose up --build
   ```
   The application will be available at `http://localhost:8000/`.

## Usage Guide

### Logging In

- Navigate to `http://localhost:8000/login/`.
- Log in using your Professor or Admin credentials.
- Provide a username and password.

### Dashboard

- Once logged in, you will see a list of courses.
- Click "Add Student" to register a new student in the system.
- Click "Manage" on a course card to view details.

### Enrolling Students

1. Go to **Course Details** (click "Manage").
2. In the "Enroll Student" card, select a student from the dropdown.
3. Click "Enroll Student".
4. If the course is full (400 capacity), you will see an error message.

### Grading & Audits

1. In **Course Details**, you will see a list of enrolled students.
2. Enter a value (0-100) in the "Grade" input field next to a student.
3. Click **Save**.
4. **Audit Mechanism**:
   - The system automatically captures the grade change.
   - If a grade existed previously, it is saved as `previous_grade` in the `GradeAudit` table.
   - You can verify this in the Admin panel (`/admin/`) under **Grade Audits**.

## API Documentation

The system provides RESTful APIs for integration.

- `POST /api/enroll/`: Enroll a student.
- `GET /api/courses/`: List courses.
- `POST /api/grades/`: Submit/Update a grade (helper endpoint).
- `GET /api/grades/`: List grades (ViewSet).

## Testing

To run the automated test suite (including concurrency and permission tests):

```bash
python manage.py test courses
```

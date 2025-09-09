
# Career Compass API

The Career Compass API provides tools and resources to guide high school students through career orientation, personalized university recommendations, and academic planning.

## Features

- Student career orientation & skills assessment
- Career guidance & pathway recommendations
- University and program matching based on student profiles
- Access to resources for informed decision-making

## Project Status Update

**September 8, 2025:** We've completed a comprehensive code review and made significant improvements to the codebase. Key improvements include:

- Fixed integration issues in catalog service
- Enhanced UUID handling across the application
- Improved error handling and logging
- Added comprehensive documentation
- Optimized services and API endpoints

For details, see the [Codebase Improvements](CODEBASE_IMPROVEMENTS.md) document.

## Project Setup

### Prerequisites

- Python 3.10+
- pip or uv (for package management)

### Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/Solvit-Africa-Training-Center/career-campass.git
   cd career-campass
   ```

2. Set up a virtual environment:
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   ```

3. Install dependencies:
   ```bash
   uv pip install -r requirements.txt
   # or with pip
   pip install -r requirements.txt
   ```

4. Configure environment variables:
   Create a `.env` file in the root directory with the following variables:
   ```
   DJANGO_SECRET_KEY=your_secret_key_here
   DJANGO_DEBUG=True  # Set to False in production
   DJANGO_ALLOWED_HOSTS=localhost,127.0.0.1
   DJANGO_EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
   DJANGO_EMAIL_HOST=smtp.gmail.com
   DJANGO_EMAIL_PORT=587
   DJANGO_EMAIL_USE_TLS=True
   DJANGO_EMAIL_HOST_USER=your_email@gmail.com
   DJANGO_EMAIL_HOST_PASSWORD=your_email_password
   DJANGO_DEFAULT_FROM_EMAIL=your_email@gmail.com
   CLOUDINARY_CLOUD_NAME=your_cloudinary_cloud_name
   CLOUDINARY_API_KEY=your_cloudinary_api_key
   CLOUDINARY_API_SECRET=your_cloudinary_api_secret
   CATALOG_BASE_URL=http://127.0.0.1:8000/api/catalog
   DOCUMENTS_BASE_URL=http://127.0.0.1:8000/documents
   HTTP_CLIENT_TIMEOUT=6.0
   ```

5. Apply migrations:
   ```bash
   python manage.py migrate
   ```

6. Create a superuser:
   ```bash
   python manage.py createsuperuser
   ```

7. Run the development server:
   ```bash
   python manage.py runserver
   ```

## API Documentation

API documentation is available at:
- Swagger UI: `/api/schema/swagger-ui/`
- ReDoc: `/api/schema/redoc/`

## Project Structure

The project is organized into several Django apps:

- **accounts**: User authentication and profile management
- **applications**: Student applications to programs
- **catalog**: Educational programs and institutions
- **core**: Project settings and shared utilities

## Key Features

### Authentication System

The application uses JWT authentication with token blacklisting:

- Register with email verification (OTP)
- Login with email/password to get access and refresh tokens
- Role-based permissions
- Token refresh and blacklisting

### UUID Implementation

The project uses UUIDs for primary keys and cross-service references:

- All models use UUIDs as primary keys
- Cross-service references use UUIDs without foreign key constraints
- Utility functions for UUID validation, parsing, and formatting

See the [UUID Guide](UUID_GUIDE.md) for details.

### API Organization

- `/api/auth/`: Authentication and user management
- `/api/applications/`: Application submission and tracking
- `/api/catalog/`: Educational programs and institutions

## Deployment

For detailed deployment instructions, see the [Deployment Guide](DEPLOYMENT_GUIDE.md).

## API Usage Examples

### Authentication

#### Register a new user

```bash
curl -X POST http://localhost:8000/api/auth/register/ \
  -H "Content-Type: application/json" \
  -d '{"email": "user@example.com", "password": "strong_password"}'
```

#### Verify email

```bash
curl -X POST http://localhost:8000/api/auth/verify-email/ \
  -H "Content-Type: application/json" \
  -d '{"email": "user@example.com", "otp": "123456"}'
```

#### Login

```bash
curl -X POST http://localhost:8000/api/auth/login/ \
  -H "Content-Type: application/json" \
  -d '{"email": "user@example.com", "password": "strong_password"}'
```

### Applications

#### Create an application

```bash
curl -X POST http://localhost:8000/api/applications/ \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <access_token>" \
  -d '{"program_id": "550e8400-e29b-41d4-a716-446655440000", "intake_id": "550e8400-e29b-41d4-a716-446655440001"}'
```

#### Get user applications

```bash
curl -X GET http://localhost:8000/api/applications/ \
  -H "Authorization: Bearer <access_token>"
```

### Catalog

#### List institutions

```bash
curl -X GET http://localhost:8000/api/catalog/institutions/
```

#### Get program details

```bash
curl -X GET http://localhost:8000/api/catalog/programs/550e8400-e29b-41d4-a716-446655440000/
```

## Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature-name`
3. Commit your changes: `git commit -am 'Add feature'`
4. Push to the branch: `git push origin feature-name`
5. Submit a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details.
curl -X POST http://localhost:8000/api/auth/login/ \
  -H "Content-Type: application/json" \
  -d '{"email": "user@example.com", "password": "strong_password"}'
```

### Applications

#### Create an application

```bash
curl -X POST http://localhost:8000/api/applications/ \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer your_access_token" \
  -d '{"program_id": "uuid_here", "intake_id": "uuid_here"}'
```

#### List applications

```bash
curl -X GET http://localhost:8000/api/applications/ \
  -H "Authorization: Bearer your_access_token"
```

#### Attach document to application

```bash
curl -X POST http://localhost:8000/api/applications/uuid_here/documents/ \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer your_access_token" \
  -d '{"doc_type_id": "uuid_here", "student_document_id": "uuid_here"}'
```

### Catalog

#### List institutions

```bash
curl -X GET http://localhost:8000/api/catalog/institutions/ \
  -H "Authorization: Bearer your_access_token"
```

#### Get program details

```bash
curl -X GET http://localhost:8000/api/catalog/programs/uuid_here/ \
  -H "Authorization: Bearer your_access_token"
```

## API Example - Application Submission

### Submit an Application

Submit a draft application after attaching all required documents:

```bash
curl -X POST http://localhost:8000/api/applications/applications/{application_id}/submit/ \
  -H "Authorization: Bearer your_access_token"
```

**Response (Success):**
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "student_id": "550e8400-e29b-41d4-a716-446655440001",
  "program_id": "550e8400-e29b-41d4-a716-446655440002",
  "intake_id": "550e8400-e29b-41d4-a716-446655440003",
  "status": "Submitted",
  "created_at": "2025-09-09T14:30:00Z",
  "updated_at": "2025-09-09T15:45:00Z"
}
```

**Error Response (Missing Documents):**
```json
{
  "detail": "Missing required documents",
  "missing_documents": [
    {
      "doc_type_id": "550e8400-e29b-41d4-a716-446655440004",
      "required": 1,
      "attached": 0
    }
  ]
}
```

## Testing

To run the tests, use the following commands:

First, set the DJANGO_SETTINGS_MODULE environment variable:

```bash
export DJANGO_SETTINGS_MODULE=core.settings
# On Windows: set DJANGO_SETTINGS_MODULE=core.settings
```

Then run:

```bash
pytest
```

**Note:**  
You may see a warning like:
```
RuntimeWarning: Model 'catalog.programfee' was already registered. Reloading models is not advised as it can lead to inconsistencies, most notably with related models.
```
This warning can be ignored if all tests pass.

## Deployment

### Production Checklist

1. Set `DEBUG=False` in environment variables
2. Configure proper `ALLOWED_HOSTS` in environment variables
3. Set up HTTPS with a valid SSL certificate
4. Use a production-ready database (PostgreSQL recommended)
5. Set up proper logging
6. Configure a reverse proxy (Nginx/Apache)
7. Set up static file serving
8. Configure database backups
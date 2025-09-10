# Career-Compass Deployment Guide

## Prerequisites

- Python 3.10 or newer
- Django 4.2 or newer
- PostgreSQL (optional, SQLite is used by default)
- UV package manager (recommended) or pip

## Environment Setup

1. Clone the repository:
   ```bash
   git clone https://github.com/Solvit-Africa-Training-Center/career-campass.git
   cd career-campass
   ```

2. Create a virtual environment:
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   ```

3. Install dependencies using UV (recommended):
   ```bash
   uv pip install -r requirements.txt
   ```
   
   Alternatively, use pip:
   ```bash
   pip install -r requirements.txt
   ```

4. Create a `.env` file in the project root with the following variables:
   ```
   DJANGO_SECRET_KEY=your-secret-key-here
   DJANGO_DEBUG=True
   DJANGO_ALLOWED_HOSTS=localhost,127.0.0.1
   HTTP_CLIENT_TIMEOUT=6.0
   CATALOG_BASE_URL=http://127.0.0.1:8000/api/catalog
   DOCUMENTS_BASE_URL=http://127.0.0.1:8000/documents
   CLOUDINARY_CLOUD_NAME=your-cloudinary-cloud-name
   CLOUDINARY_API_KEY=your-cloudinary-api-key
   CLOUDINARY_API_SECRET=your-cloudinary-api-secret
   DJANGO_EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
   DJANGO_EMAIL_HOST=smtp.gmail.com
   DJANGO_EMAIL_PORT=587
   DJANGO_EMAIL_USE_TLS=True
   DJANGO_EMAIL_HOST_USER=your-email@gmail.com
   DJANGO_EMAIL_HOST_PASSWORD=your-email-password
   DJANGO_DEFAULT_FROM_EMAIL=your-email@gmail.com
   ```

   For production, make sure to:
   - Use a strong, unique secret key
   - Set DEBUG=False
   - Set appropriate ALLOWED_HOSTS
   - Configure a production database
   - Set up proper email credentials

## Database Setup

By default, the application uses SQLite. For production, it's recommended to use PostgreSQL:

1. Install PostgreSQL and create a database:
   ```bash
   sudo apt-get install postgresql postgresql-contrib
   sudo -u postgres createdb career_compass
   sudo -u postgres createuser -P career_compass_user
   ```

2. Add the database configuration to your `.env` file:
   ```
   DATABASE_URL=postgres://career_compass_user:password@localhost:5432/career_compass
   ```

3. Run migrations:
   ```bash
   python manage.py migrate
   ```

## Create a Superuser

Create an admin user to access the Django admin interface:
```bash
python manage.py createsuperuser
```

## Running the Application

1. Start the development server:
   ```bash
   python manage.py runserver
   ```

2. Access the API at http://127.0.0.1:8000/api/

3. Access the API documentation at:
   - Swagger UI: http://127.0.0.1:8000/api/schema/swagger-ui/
   - ReDoc: http://127.0.0.1:8000/api/schema/redoc/

## API Endpoints Overview

### Authentication Endpoints
- `POST /api/auth/register/`: Register a new user
- `POST /api/auth/verify-email/`: Verify email with OTP
- `POST /api/auth/resend-otp/`: Resend OTP for email verification
- `POST /api/auth/login/`: Login and get JWT tokens
- `POST /api/auth/logout/`: Logout and blacklist token
- `POST /api/auth/token/refresh/`: Refresh JWT token

### User Management Endpoints
- `GET /api/auth/users/`: List users (requires authentication)
- `GET /api/auth/profiles/`: List profiles (requires authentication)
- `GET /api/auth/students/`: List students (requires authentication)
- `GET /api/auth/agents/`: List agents (requires authentication)
- `GET /api/auth/roles/`: List roles (requires authentication)

### Application Endpoints
- `GET /api/applications/`: List user applications (requires authentication)
- `POST /api/applications/`: Create a new application
- `POST /api/applications/{id}/documents/`: Attach document to application

### Catalog Endpoints
- `GET /api/catalog/institutions/`: List institutions
- `GET /api/catalog/programs/`: List programs
- `GET /api/catalog/intakes/`: List program intakes
- `GET /api/catalog/fees/`: List program fees
- `GET /api/catalog/requirements/`: List admission requirements

## Production Deployment

For production deployment, consider:

1. Using Gunicorn as the WSGI server:
   ```bash
   pip install gunicorn
   gunicorn core.wsgi:application
   ```

2. Setting up Nginx as a reverse proxy:
   ```nginx
   server {
       listen 80;
       server_name yourdomainname.com;

       location /static/ {
           root /path/to/career-campass;
       }

       location / {
           proxy_pass http://127.0.0.1:8000;
           proxy_set_header Host $host;
           proxy_set_header X-Real-IP $remote_addr;
       }
   }
   ```

3. Setting up SSL with Let's Encrypt:
   ```bash
   sudo apt-get install certbot python3-certbot-nginx
   sudo certbot --nginx -d yourdomainname.com
   ```

4. Setting up a process manager like Supervisor:
   ```ini
   [program:career-compass]
   command=/path/to/venv/bin/gunicorn --workers 3 --bind 127.0.0.1:8000 core.wsgi:application
   directory=/path/to/career-campass
   autostart=true
   autorestart=true
   stderr_logfile=/var/log/career-compass/error.log
   stdout_logfile=/var/log/career-compass/access.log
   user=www-data
   environment=DJANGO_SECRET_KEY="yoursecretkey",DJANGO_DEBUG="False",...
   ```

## Troubleshooting

1. **Database Migration Issues**:
   ```bash
   python manage.py showmigrations  # Check migration status
   python manage.py migrate --fake-initial  # If migrations are in inconsistent state
   ```

2. **Static Files Not Loading**:
   ```bash
   python manage.py collectstatic  # Collect static files
   ```

3. **Email Sending Issues**:
   - Check email credentials in .env
   - For Gmail, enable "Less secure apps" or use App Passwords

4. **API Connection Issues**:
   - Check network connectivity
   - Verify correct URLs in .env
   - Check firewall settings

## Maintenance

1. Backup your database regularly:
   ```bash
   pg_dump -U career_compass_user career_compass > backup_$(date +%Y-%m-%d).sql
   ```

2. Update dependencies periodically:
   ```bash
   uv pip install -r requirements.txt --upgrade
   ```

3. Check for security vulnerabilities:
   ```bash
   uv pip install safety
   safety check
   ```

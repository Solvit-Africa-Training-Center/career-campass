# Career Compass Deployment Guide

This guide provides detailed instructions for deploying the Career Compass API to production environments.

## Deployment Options

### 1. Traditional Server Deployment

#### Prerequisites
- Ubuntu 20.04 LTS or newer
- Python 3.8+
- PostgreSQL 12+
- Nginx
- Let's Encrypt SSL certificate
- Domain name pointing to your server

#### Installation Steps

1. **Update and install system packages**
   ```bash
   sudo apt update
   sudo apt upgrade -y
   sudo apt install -y python3-pip python3-venv nginx postgresql postgresql-contrib
   ```

2. **Create a PostgreSQL database**
   ```bash
   sudo -u postgres psql
   CREATE DATABASE career_compass;
   CREATE USER career_compass_user WITH PASSWORD 'secure_password';
   ALTER ROLE career_compass_user SET client_encoding TO 'utf8';
   ALTER ROLE career_compass_user SET default_transaction_isolation TO 'read committed';
   ALTER ROLE career_compass_user SET timezone TO 'UTC';
   GRANT ALL PRIVILEGES ON DATABASE career_compass TO career_compass_user;
   \q
   ```

3. **Clone the repository**
   ```bash
   git clone https://github.com/Solvit-Africa-Training-Center/career-campass.git
   cd career-campass
   ```

4. **Create and activate virtual environment**
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   ```

5. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   pip install gunicorn psycopg2-binary
   ```

6. **Create .env file**
   ```bash
   cat > .env << EOF
   DJANGO_SECRET_KEY=your_secure_secret_key_here
   DJANGO_DEBUG=False
   DJANGO_ALLOWED_HOSTS=yourdomainname.com,www.yourdomainname.com
   DATABASE_URL=postgres://career_compass_user:secure_password@localhost:5432/career_compass
   DJANGO_EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
   DJANGO_EMAIL_HOST=smtp.gmail.com
   DJANGO_EMAIL_PORT=587
   DJANGO_EMAIL_USE_TLS=True
   DJANGO_EMAIL_HOST_USER=your_email@gmail.com
   DJANGO_EMAIL_HOST_PASSWORD=your_app_password_here
   DJANGO_DEFAULT_FROM_EMAIL=your_email@gmail.com
   CLOUDINARY_CLOUD_NAME=your_cloudinary_cloud_name
   CLOUDINARY_API_KEY=your_cloudinary_api_key
   CLOUDINARY_API_SECRET=your_cloudinary_api_secret
   HTTP_CLIENT_TIMEOUT=10.0
   EOF
   ```

7. **Update settings.py to use PostgreSQL**
   Add to your core/settings.py:
   ```python
   import dj_database_url
   
   # Use DATABASE_URL environment variable if available
   if os.getenv('DATABASE_URL'):
       DATABASES = {
           'default': dj_database_url.config(
               default=os.getenv('DATABASE_URL')
           )
       }
   ```

8. **Run migrations and create superuser**
   ```bash
   python manage.py migrate
   python manage.py createsuperuser
   python manage.py collectstatic
   ```

9. **Configure Gunicorn service**
   ```bash
   sudo nano /etc/systemd/system/career-compass.service
   ```
   Add the following content:
   ```
   [Unit]
   Description=Career Compass API Gunicorn Service
   After=network.target
   
   [Service]
   User=ubuntu
   Group=www-data
   WorkingDirectory=/path/to/career-campass
   ExecStart=/path/to/career-campass/venv/bin/gunicorn \
             --access-logfile - \
             --workers 3 \
             --bind unix:/path/to/career-campass/career-compass.sock \
             core.wsgi:application
   Restart=on-failure
   EnvironmentFile=/path/to/career-campass/.env
   
   [Install]
   WantedBy=multi-user.target
   ```

10. **Enable and start Gunicorn service**
    ```bash
    sudo systemctl start career-compass
    sudo systemctl enable career-compass
    ```

11. **Configure Nginx**
    ```bash
    sudo nano /etc/nginx/sites-available/career-compass
    ```
    Add the following content:
    ```
    server {
        listen 80;
        server_name yourdomainname.com www.yourdomainname.com;
        
        location = /favicon.ico { access_log off; log_not_found off; }
        
        location /static/ {
            root /path/to/career-campass;
        }
        
        location / {
            include proxy_params;
            proxy_pass http://unix:/path/to/career-campass/career-compass.sock;
        }
    }
    ```

12. **Enable the Nginx configuration and test**
    ```bash
    sudo ln -s /etc/nginx/sites-available/career-compass /etc/nginx/sites-enabled/
    sudo nginx -t
    sudo systemctl restart nginx
    ```

13. **Set up SSL with Let's Encrypt**
    ```bash
    sudo apt install -y certbot python3-certbot-nginx
    sudo certbot --nginx -d yourdomainname.com -d www.yourdomainname.com
    ```

### 2. Docker Deployment

#### Prerequisites
- Docker
- Docker Compose
- A server with Docker installed
- Domain name pointing to your server

#### Setup

1. **Create a Dockerfile**
   Create this file in the project root:
   ```Dockerfile
   FROM python:3.11-slim
   
   WORKDIR /app
   
   COPY requirements.txt .
   RUN pip install --no-cache-dir -r requirements.txt
   RUN pip install gunicorn psycopg2-binary
   
   COPY . .
   
   RUN python manage.py collectstatic --noinput
   
   EXPOSE 8000
   
   CMD ["gunicorn", "core.wsgi:application", "--bind", "0.0.0.0:8000"]
   ```

2. **Create a docker-compose.yml file**
   ```yaml
   version: '3'
   
   services:
     db:
       image: postgres:14
       volumes:
         - postgres_data:/var/lib/postgresql/data/
       env_file:
         - ./.env
       environment:
         - POSTGRES_PASSWORD=postgres
         - POSTGRES_USER=postgres
         - POSTGRES_DB=career_compass
       restart: always
   
     web:
       build: .
       restart: always
       depends_on:
         - db
       env_file:
         - ./.env
       environment:
         - DATABASE_URL=postgres://postgres:postgres@db:5432/career_compass
       volumes:
         - static_volume:/app/staticfiles
       command: >
         bash -c "python manage.py migrate &&
                 gunicorn core.wsgi:application --bind 0.0.0.0:8000"
   
     nginx:
       image: nginx:1.21
       ports:
         - "80:80"
         - "443:443"
       volumes:
         - static_volume:/app/staticfiles
         - ./nginx:/etc/nginx/conf.d
         - ./certbot/www:/var/www/certbot
         - ./certbot/conf:/etc/letsencrypt
       depends_on:
         - web
   
     certbot:
       image: certbot/certbot
       volumes:
         - ./certbot/www:/var/www/certbot
         - ./certbot/conf:/etc/letsencrypt
       entrypoint: "/bin/sh -c 'trap exit TERM; while :; do certbot renew; sleep 12h & wait $${!}; done;'"
   
   volumes:
     postgres_data:
     static_volume:
   ```

3. **Create Nginx configuration**
   ```bash
   mkdir -p nginx certbot/www certbot/conf
   ```
   
   Create nginx/default.conf:
   ```
   server {
       listen 80;
       server_name yourdomainname.com www.yourdomainname.com;
       
       location /.well-known/acme-challenge/ {
           root /var/www/certbot;
       }
       
       location / {
           return 301 https://$host$request_uri;
       }
   }
   
   server {
       listen 443 ssl;
       server_name yourdomainname.com www.yourdomainname.com;
       
       ssl_certificate /etc/letsencrypt/live/yourdomainname.com/fullchain.pem;
       ssl_certificate_key /etc/letsencrypt/live/yourdomainname.com/privkey.pem;
       
       location /static/ {
           alias /app/staticfiles/;
       }
       
       location / {
           proxy_pass http://web:8000;
           proxy_set_header Host $host;
           proxy_set_header X-Real-IP $remote_addr;
       }
   }
   ```

4. **Create an .env file**
   ```
   DJANGO_SECRET_KEY=your_secure_secret_key_here
   DJANGO_DEBUG=False
   DJANGO_ALLOWED_HOSTS=yourdomainname.com,www.yourdomainname.com
   DJANGO_EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
   DJANGO_EMAIL_HOST=smtp.gmail.com
   DJANGO_EMAIL_PORT=587
   DJANGO_EMAIL_USE_TLS=True
   DJANGO_EMAIL_HOST_USER=your_email@gmail.com
   DJANGO_EMAIL_HOST_PASSWORD=your_app_password_here
   DJANGO_DEFAULT_FROM_EMAIL=your_email@gmail.com
   CLOUDINARY_CLOUD_NAME=your_cloudinary_cloud_name
   CLOUDINARY_API_KEY=your_cloudinary_api_key
   CLOUDINARY_API_SECRET=your_cloudinary_api_secret
   HTTP_CLIENT_TIMEOUT=10.0
   ```

5. **Initial deployment**
   ```bash
   # Start only with HTTP to get SSL certificates
   docker-compose up -d nginx
   
   # Get SSL certificate
   docker-compose run --rm certbot certonly --webroot -w /var/www/certbot -d yourdomainname.com -d www.yourdomainname.com
   
   # Restart everything
   docker-compose down
   docker-compose up -d
   ```

## Monitoring and Maintenance

### Logging

Set up logging in your Django settings:

```python
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'file': {
            'level': 'INFO',
            'class': 'logging.FileHandler',
            'filename': os.path.join(BASE_DIR, 'logs/debug.log'),
            'formatter': 'verbose',
        },
    },
    'loggers': {
        'django': {
            'handlers': ['file'],
            'level': 'INFO',
            'propagate': True,
        },
    },
}
```

### Backups

Set up a cron job to backup the database daily:

```bash
# Add to crontab
0 2 * * * /path/to/backup_script.sh
```

Create a backup script:
```bash
#!/bin/bash
BACKUP_DIR="/path/to/backups"
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
PGDUMP_PATH="pg_dump"
DATABASE="career_compass"
USERNAME="career_compass_user"
PASSWORD="secure_password"

# Create backup directory if it doesn't exist
mkdir -p $BACKUP_DIR

# Backup filename
BACKUP_FILE="$BACKUP_DIR/db_backup_$TIMESTAMP.sql.gz"

# Create backup
PGPASSWORD=$PASSWORD $PGDUMP_PATH -U $USERNAME -d $DATABASE | gzip > $BACKUP_FILE

# Delete backups older than 14 days
find $BACKUP_DIR -type f -name "db_backup_*.sql.gz" -mtime +14 -delete
```

### Security Best Practices

1. **Regular updates**
   ```bash
   # Update system packages
   sudo apt update && sudo apt upgrade -y
   
   # Update Python packages
   pip install --upgrade -r requirements.txt
   ```

2. **Firewall configuration**
   ```bash
   sudo ufw allow ssh
   sudo ufw allow http
   sudo ufw allow https
   sudo ufw enable
   ```

3. **Regular security scans**
   ```bash
   # Install security scanner
   pip install safety
   
   # Run scan
   safety check
   ```

4. **Rate limiting**
   Add Django-ratelimit to limit API requests
   
   ```python
   # In views.py
   from ratelimit.decorators import ratelimit
   
   @ratelimit(key='ip', rate='100/h')
   def view_func(request):
       pass
   ```

## Performance Optimization

1. **Add caching**
   ```python
   CACHES = {
       'default': {
           'BACKEND': 'django.core.cache.backends.redis.RedisCache',
           'LOCATION': 'redis://127.0.0.1:6379/1',
           'TIMEOUT': 300,
       }
   }
   ```

2. **Database optimization**
   ```sql
   -- Check slow queries
   SELECT query, calls, total_time, mean_time
   FROM pg_stat_statements
   ORDER BY mean_time DESC
   LIMIT 10;
   
   -- Add appropriate indexes based on query patterns
   ```

3. **Configure connection pooling**
   Install django-db-connection-pool and configure in settings:
   ```python
   DATABASES = {
       'default': {
           'ENGINE': 'dj_db_conn_pool.backends.postgresql',
           'NAME': 'career_compass',
           'POOL_OPTIONS': {
               'POOL_SIZE': 20,
               'MAX_OVERFLOW': 10,
               'RECYCLE': 300,
           },
       }
   }
   ```

## Troubleshooting

### Common Issues and Solutions

1. **502 Bad Gateway**
   - Check Gunicorn is running: `sudo systemctl status career-compass`
   - Check socket permissions: `ls -la /path/to/career-campass/career-compass.sock`
   - Check Nginx config: `sudo nginx -t`

2. **Database connection errors**
   - Verify PostgreSQL is running: `sudo systemctl status postgresql`
   - Check connection parameters in .env file
   - Verify network connectivity between services

3. **Static files not loading**
   - Ensure collectstatic was run: `python manage.py collectstatic`
   - Check static file paths in settings.py and Nginx config
   - Verify file permissions

4. **Email not sending**
   - Verify SMTP credentials
   - Test connection: `python -m smtplib -d your.smtp.server 587`
   - Check email service dashboard for sending limits

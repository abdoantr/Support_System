# Deployment Checklist

This document provides a checklist for deploying the Support System application to a production environment.

## Pre-Deployment Checks

1. **Run the production settings check:**

   ```bash
   python manage.py check_production_settings
   ```

   Fix any errors or warnings before proceeding.

2. **Generate a new secret key:**

   ```bash
   python manage.py generate_secret_key --update-env
   ```

3. **Update the .env file for production:**

   - Set `DEBUG=False`
   - Add your production domain to `ALLOWED_HOSTS`
   - Configure proper database credentials
   - Set up email credentials

4. **Run tests to ensure everything works:**

   ```bash
   python manage.py test
   ```

## Database Configuration

1. **Create a production database:**

   - For MySQL:
     ```sql
     CREATE DATABASE supportsystem CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
     CREATE USER 'support_user'@'localhost' IDENTIFIED BY 'your_strong_password';
     GRANT ALL PRIVILEGES ON supportsystem.* TO 'support_user'@'localhost';
     FLUSH PRIVILEGES;
     ```

2. **Run migrations:**

   ```bash
   python manage.py migrate
   ```

3. **Create a superuser:**

   ```bash
   python manage.py createsuperuser
   ```

## Static Files and Media

1. **Collect static files:**

   ```bash
   python manage.py collectstatic --no-input
   ```

2. **Configure the web server to serve static files and media:**

   - For Nginx, add to your server block:
     ```
     location /static/ {
         alias /path/to/your/staticfiles/;
     }

     location /media/ {
         alias /path/to/your/media/;
     }
     ```

## Web Server and WSGI/ASGI Configuration

1. **Configure Gunicorn (WSGI):**

   ```bash
   gunicorn --bind 0.0.0.0:8000 config.wsgi:application
   ```

   Create a systemd service file for auto-start:

   ```ini
   [Unit]
   Description=Support System Gunicorn daemon
   After=network.target

   [Service]
   User=www-data
   Group=www-data
   WorkingDirectory=/path/to/your/project
   ExecStart=/path/to/your/venv/bin/gunicorn --bind 0.0.0.0:8000 config.wsgi:application
   Restart=on-failure

   [Install]
   WantedBy=multi-user.target
   ```

2. **Configure Nginx as a reverse proxy:**

   ```nginx
   server {
       listen 80;
       server_name your-domain.com;

       # Redirect HTTP to HTTPS
       return 301 https://$host$request_uri;
   }

   server {
       listen 443 ssl;
       server_name your-domain.com;

       ssl_certificate /path/to/ssl/certificate.crt;
       ssl_certificate_key /path/to/ssl/private.key;

       location = /favicon.ico { access_log off; log_not_found off; }
       
       location /static/ {
           alias /path/to/your/staticfiles/;
       }

       location /media/ {
           alias /path/to/your/media/;
       }

       location / {
           proxy_set_header Host $http_host;
           proxy_set_header X-Real-IP $remote_addr;
           proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
           proxy_set_header X-Forwarded-Proto $scheme;
           proxy_pass http://localhost:8000;
       }
   }
   ```

## Celery Configuration

1. **Configure Celery as a service:**

   Create a systemd service file:

   ```ini
   [Unit]
   Description=Support System Celery Service
   After=network.target

   [Service]
   User=www-data
   Group=www-data
   WorkingDirectory=/path/to/your/project
   ExecStart=/path/to/your/venv/bin/celery -A config worker -l info
   Restart=on-failure

   [Install]
   WantedBy=multi-user.target
   ```

2. **Configure Celery Beat as a service:**

   ```ini
   [Unit]
   Description=Support System Celery Beat Service
   After=network.target

   [Service]
   User=www-data
   Group=www-data
   WorkingDirectory=/path/to/your/project
   ExecStart=/path/to/your/venv/bin/celery -A config beat -l info
   Restart=on-failure

   [Install]
   WantedBy=multi-user.target
   ```

## Post-Deployment Checks

1. **Verify the site is accessible**
2. **Check SSL configuration using SSL Labs**
3. **Verify email functionality**
4. **Test ticket creation and management**
5. **Monitor application logs for errors**
6. **Set up regular database backups**

## Maintenance

1. **Configure log rotation:**

   ```
   /path/to/your/project/logs/*.log {
       daily
       missingok
       rotate 14
       compress
       delaycompress
       notifempty
       create 0640 www-data www-data
   }
   ```

2. **Set up automated backups for the database**
3. **Configure monitoring for the application (e.g., Prometheus, Grafana)**
4. **Set up regular security updates for the server** 
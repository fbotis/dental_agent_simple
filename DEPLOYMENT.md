# Docker Deployment Guide

This guide covers deploying the Dental Clinic Assistant to a VPS using Docker.

## Prerequisites

- Docker installed on your VPS
- Docker Compose installed (optional, but recommended)
- SSH access to your VPS
- Required API keys (see Environment Variables section)

## Quick Start

### 1. Transfer Files to VPS

```bash
# On your local machine
rsync -avz --exclude='.venv' --exclude='__pycache__' \
  --exclude='conversations' --exclude='recordings' \
  . user@your-vps-ip:/opt/dental-assistant/
```

### 2. Set Up Environment Variables

```bash
# On your VPS
cd /opt/dental-assistant
cp .env.example .env
nano .env  # Edit with your API keys
```

Required environment variables:
```bash
# Core LLM
OPENAI_API_KEY=your_openai_key_here

# For Voice Assistant (Optional)
CARTESIA_API_KEY=your_cartesia_key_here
DEEPGRAM_API_KEY=your_deepgram_key_here
DAILY_API_KEY=your_daily_key_here

# For Telegram Bot (Optional)
TELEGRAM_BOT_TOKEN=your_telegram_token_here

# Appointment System (Optional)
APPOINTMENT_SYSTEM_TYPE=mock  # or google_calendar
```

### 3. Build and Run with Docker Compose

```bash
# Build the image
docker-compose build

# Start the service
docker-compose up -d

# View logs
docker-compose logs -f

# Stop the service
docker-compose down
```

## Manual Docker Commands

If you prefer not to use Docker Compose:

### Build the Image

```bash
docker build -t dental-assistant:latest .
```

### Run the Container

```bash
docker run -d \
  --name dental-clinic-assistant \
  --restart unless-stopped \
  --env-file .env \
  -v $(pwd)/conversations:/app/conversations \
  -v $(pwd)/recordings:/app/recordings \
  -v $(pwd)/metrics.log:/app/metrics.log \
  -p 8080:8080 \
  dental-assistant:latest
```

### View Logs

```bash
docker logs -f dental-clinic-assistant
```

### Stop and Remove

```bash
docker stop dental-clinic-assistant
docker rm dental-clinic-assistant
```

## Production Deployment

### Using a Reverse Proxy (Nginx)

If your application exposes a web interface:

```nginx
# /etc/nginx/sites-available/dental-assistant
server {
    listen 80;
    server_name your-domain.com;

    location / {
        proxy_pass http://localhost:8080;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_cache_bypass $http_upgrade;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    }
}
```

Enable SSL with Let's Encrypt:
```bash
sudo certbot --nginx -d your-domain.com
```

### Systemd Service (Alternative to Docker Compose)

Create `/etc/systemd/system/dental-assistant.service`:

```ini
[Unit]
Description=Dental Clinic Assistant
Requires=docker.service
After=docker.service

[Service]
Type=oneshot
RemainAfterExit=yes
WorkingDirectory=/opt/dental-assistant
ExecStart=/usr/bin/docker-compose up -d
ExecStop=/usr/bin/docker-compose down
TimeoutStartSec=0

[Install]
WantedBy=multi-user.target
```

Enable and start:
```bash
sudo systemctl enable dental-assistant
sudo systemctl start dental-assistant
```

## Updating the Application

```bash
# Pull latest code
git pull

# Rebuild and restart
docker-compose down
docker-compose build --no-cache
docker-compose up -d
```

## Monitoring and Maintenance

### View Application Logs

```bash
docker-compose logs -f dental-assistant
```

### Check Resource Usage

```bash
docker stats dental-clinic-assistant
```

### Backup Data

```bash
# Backup conversations and recordings
tar -czf backup-$(date +%Y%m%d).tar.gz conversations/ recordings/ metrics.log

# Copy to safe location
scp backup-*.tar.gz backup-server:/backups/
```

### Clean Up Docker Resources

```bash
# Remove unused images
docker image prune -a

# Remove unused volumes
docker volume prune

# Complete cleanup (be careful!)
docker system prune -a
```

## Troubleshooting

### Container Won't Start

```bash
# Check logs for errors
docker-compose logs dental-assistant

# Verify environment variables
docker-compose config

# Check if port is already in use
sudo netstat -tulpn | grep 8080
```

### Permission Issues with Volumes

```bash
# Fix permissions
sudo chown -R 1000:1000 conversations recordings
```

### Out of Memory

```bash
# Limit memory in docker-compose.yml
services:
  dental-assistant:
    deploy:
      resources:
        limits:
          memory: 2G
```

### Application Crashes

```bash
# Check container status
docker ps -a

# View full logs
docker logs dental-clinic-assistant --tail 100

# Restart container
docker-compose restart
```

## Security Best Practices

1. **Never commit `.env` file** - It contains sensitive API keys
2. **Use secrets management** - Consider Docker secrets or environment variable injection
3. **Keep images updated** - Regularly rebuild with latest base images
4. **Limit network exposure** - Only expose necessary ports
5. **Use non-root user** - Consider adding USER directive in Dockerfile
6. **Enable firewall** - Use UFW or iptables to restrict access

```bash
# Example UFW rules
sudo ufw allow 22/tcp   # SSH
sudo ufw allow 80/tcp   # HTTP
sudo ufw allow 443/tcp  # HTTPS
sudo ufw enable
```

## Multi-Environment Setup

### Development
```bash
docker-compose -f docker-compose.dev.yml up
```

### Production
```bash
docker-compose -f docker-compose.prod.yml up -d
```

## Performance Optimization

1. **Multi-stage builds** - Reduce image size
2. **Layer caching** - Order Dockerfile commands efficiently
3. **Health checks** - Monitor application status
4. **Resource limits** - Prevent resource exhaustion
5. **Logging strategy** - Use proper log rotation

## Support

For issues or questions:
- Check application logs
- Review environment variables
- Verify API keys are valid
- Ensure all dependencies are installed

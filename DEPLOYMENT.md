# Production Deployment Guide

This guide explains how to deploy datagusto to production using Docker Compose with automatic HTTPS via Let's Encrypt.

## Prerequisites

- A Linux server (Ubuntu 20.04+ recommended)
- Docker and Docker Compose installed
- Domain names pointing to your server's IP address:
  - `app.datagusto.io` - For the web application
  - `api.datagusto.io` - For the API backend
- Valid email address for Let's Encrypt notifications

## Deployment Steps

### 1. Clone the Repository

```bash
git clone https://github.com/your-org/datagusto-platform-prod.git
cd datagusto-platform-prod
```

### 2. Configure Environment Variables

```bash
cp .env.production.example .env.production
nano .env.production
```

**REQUIRED Configuration:**
```bash
# Generate secure JWT keys
JWT_SECRET_KEY=$(openssl rand -hex 32)
JWT_REFRESH_SECRET_KEY=$(openssl rand -hex 32)
echo "JWT_SECRET_KEY=$JWT_SECRET_KEY"
echo "JWT_REFRESH_SECRET_KEY=$JWT_REFRESH_SECRET_KEY"
```

Update the following critical values:
- `POSTGRES_PASSWORD` - Use a strong, random password (minimum 16 characters)
- `JWT_SECRET_KEY` - Use the generated key above (REQUIRED)
- `JWT_REFRESH_SECRET_KEY` - Use the generated key above (REQUIRED)
- `LETSENCRYPT_EMAIL` - Your email for SSL certificate notifications
- External service keys if needed (Langfuse, OpenAI)

**Security Validation:**
- JWT keys must be at least 32 characters long
- PostgreSQL password should be strong and unique
- Never use default values in production

### 3. Create Required Directories

```bash
# Create directories for nginx-proxy
mkdir -p nginx/{conf.d,vhost.d,html,certs}
```

### 4. Environment Validation

Before deployment, validate your configuration:

```bash
# Check if required files exist
test -f .env.production || echo "❌ .env.production not found"

# Validate JWT keys are set
source .env.production
test -n "$JWT_SECRET_KEY" || echo "❌ JWT_SECRET_KEY not set"
test -n "$JWT_REFRESH_SECRET_KEY" || echo "❌ JWT_REFRESH_SECRET_KEY not set"
test -n "$POSTGRES_PASSWORD" || echo "❌ POSTGRES_PASSWORD not set"
test -n "$LETSENCRYPT_EMAIL" || echo "❌ LETSENCRYPT_EMAIL not set"

# Validate JWT key length (should be 64 characters for hex)
test ${#JWT_SECRET_KEY} -eq 64 || echo "⚠️ JWT_SECRET_KEY should be 64 characters"
test ${#JWT_REFRESH_SECRET_KEY} -eq 64 || echo "⚠️ JWT_REFRESH_SECRET_KEY should be 64 characters"
```

### 5. Build and Start Services

With nginx-proxy and Let's Encrypt companion, SSL certificates will be automatically generated and renewed.

```bash
# Build images
docker compose -f docker-compose.prod.yml build

# Start services
docker compose -f docker-compose.prod.yml up -d

# Check service status
docker compose -f docker-compose.prod.yml ps

# View logs
docker compose -f docker-compose.prod.yml logs -f
```

### 6. Verify Deployment

1. **Check if services are running:**
   ```bash
   docker compose -f docker-compose.prod.yml ps
   ```

2. **Monitor SSL certificate generation:**
   ```bash
   # Watch Let's Encrypt logs for certificate generation
   docker compose -f docker-compose.prod.yml logs -f letsencrypt
   
   # Check nginx-proxy logs
   docker compose -f docker-compose.prod.yml logs nginx-proxy
   ```

3. **Test endpoints:**
   ```bash
   # Test API endpoint (may take a few minutes for SSL to be ready)
   curl https://api.datagusto.io/docs
   
   # Test frontend
   curl -I https://app.datagusto.io
   ```

4. **Access the applications:**
   - Frontend: https://app.datagusto.io
   - API Documentation: https://api.datagusto.io/docs

5. **Initial SSL Certificate Generation:**
   - First deployment may take 2-5 minutes for SSL certificates
   - Monitor logs with: `docker compose -f docker-compose.prod.yml logs letsencrypt`
   - Certificates will auto-renew before expiration

## Maintenance

### Viewing Logs

```bash
# All services
docker compose -f docker-compose.prod.yml logs -f

# Specific service
docker compose -f docker-compose.prod.yml logs -f backend
docker compose -f docker-compose.prod.yml logs -f frontend
docker compose -f docker-compose.prod.yml logs -f nginx
```

### Updating the Application

```bash
# Pull latest changes
git pull origin main

# Rebuild and restart services
docker compose -f docker-compose.prod.yml build
docker compose -f docker-compose.prod.yml up -d
```

### Database Backup

```bash
# Create backup
docker compose -f docker-compose.prod.yml exec postgres \
  pg_dump -U postgres datagusto > backup_$(date +%Y%m%d_%H%M%S).sql

# Restore backup
docker compose -f docker-compose.prod.yml exec -T postgres \
  psql -U postgres datagusto < backup_20240101_120000.sql
```

### SSL Certificate Management

Let's Encrypt certificates are automatically renewed by the letsencrypt-nginx-proxy-companion container. No manual intervention is required.

To check certificate status:
```bash
docker compose -f docker-compose.prod.yml logs letsencrypt
```

## Troubleshooting

### Services Not Starting

1. Check logs: `docker compose -f docker-compose.prod.yml logs`
2. Verify environment variables are set correctly
3. Ensure ports 80 and 443 are not in use: `sudo netstat -tlnp | grep -E ':80|:443'`

### SSL Issues

1. Check Let's Encrypt logs: `docker compose -f docker-compose.prod.yml logs letsencrypt`
2. Verify domains are pointing to your server's IP
3. Check nginx-proxy logs: `docker compose -f docker-compose.prod.yml logs nginx-proxy`
4. Test SSL configuration: https://www.ssllabs.com/ssltest/
5. Ensure ports 80 and 443 are open in your firewall

### Database Connection Issues

1. Check if postgres is running: `docker compose -f docker-compose.prod.yml ps postgres`
2. Verify DATABASE_URL in backend logs
3. Test connection: `docker compose -f docker-compose.prod.yml exec postgres psql -U postgres -d datagusto`

## Security Recommendations

### 1. Firewall Setup
```bash
sudo ufw allow 22/tcp  # SSH
sudo ufw allow 80/tcp  # HTTP (redirects to HTTPS)
sudo ufw allow 443/tcp # HTTPS
sudo ufw enable
```

### 2. Security Configuration Checklist

**✅ Implemented Security Features:**
- Separate JWT secrets for access and refresh tokens
- CORS configured for production domains only
- PostgreSQL isolated within Docker network (no external ports)
- HTTPS enforced with automatic SSL certificates
- Security headers configured via nginx-proxy
- Non-root users in Docker containers
- Environment variable validation

**📋 Additional Recommendations:**
- Change default PostgreSQL port if exposing externally
- Enable Docker secret management for sensitive data
- Implement log rotation for container logs
- Set up monitoring and alerting
- Regular security audits of dependencies

### 3. Environment Security
```bash
# Validate production configuration
grep -E "^[A-Z_]+=.+" .env.production | while read line; do
  key=$(echo "$line" | cut -d'=' -f1)
  value=$(echo "$line" | cut -d'=' -f2-)
  case "$key" in
    *PASSWORD*|*SECRET*|*KEY*)
      if [[ ${#value} -lt 16 ]]; then
        echo "⚠️ $key is too short (less than 16 characters)"
      fi
      ;;
  esac
done
```

### 4. Regular Maintenance
- **System Updates**: Keep Docker and OS packages updated
- **Image Updates**: Rebuild images monthly for security patches
- **Certificate Monitoring**: Let's Encrypt handles renewal automatically
- **Log Monitoring**: Check logs for suspicious activity
- **Backup Strategy**: Automate database backups and test restore procedures
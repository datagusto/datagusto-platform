# SSL Certificate Directory

This directory is used by nginx-proxy and letsencrypt-nginx-proxy-companion to store SSL certificates.

## Automatic SSL with Let's Encrypt

When using the production Docker Compose setup, SSL certificates are automatically:
- Generated on first deployment
- Renewed before expiration
- Stored in this directory

No manual certificate management is required.

## How it works

1. The `letsencrypt-nginx-proxy-companion` container monitors for new containers with `LETSENCRYPT_HOST` environment variables
2. It automatically requests certificates from Let's Encrypt for those domains
3. Certificates are stored in this directory and used by nginx-proxy
4. Renewal happens automatically before expiration

## Important Notes:
- Never commit certificates to version control
- This directory should have proper permissions (handled by Docker)
- Certificates are domain-specific and generated per deployment
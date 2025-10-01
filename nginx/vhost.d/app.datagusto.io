# Security headers for app.datagusto.io
add_header X-Frame-Options "SAMEORIGIN" always;
add_header X-Content-Type-Options "nosniff" always;
add_header X-XSS-Protection "1; mode=block" always;
add_header Referrer-Policy "strict-origin-when-cross-origin" always;
add_header Strict-Transport-Security "max-age=31536000; includeSubDomains; preload" always;
add_header Content-Security-Policy "default-src 'self'; script-src 'self' 'unsafe-inline' 'unsafe-eval'; style-src 'self' 'unsafe-inline'; img-src 'self' data: https:; font-src 'self' data:; connect-src 'self' https://api.datagusto.io wss://api.datagusto.io; frame-ancestors 'none';" always;

# Proxy timeout settings for frontend
proxy_connect_timeout 120s;
proxy_send_timeout 120s;
proxy_read_timeout 120s;
send_timeout 120s;

# Buffer settings
proxy_buffer_size 16k;
proxy_buffers 16 16k;
proxy_busy_buffers_size 32k;
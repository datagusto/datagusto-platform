# Security headers for api.datagusto.io
add_header X-Frame-Options "DENY" always;
add_header X-Content-Type-Options "nosniff" always;
add_header X-XSS-Protection "1; mode=block" always;
add_header Referrer-Policy "strict-origin-when-cross-origin" always;
add_header Strict-Transport-Security "max-age=31536000; includeSubDomains; preload" always;

# Proxy timeout settings for API endpoints
proxy_connect_timeout 300s;
proxy_send_timeout 300s;  
proxy_read_timeout 300s;
send_timeout 300s;

# Buffer settings for large requests/responses
proxy_buffer_size 32k;
proxy_buffers 32 32k;
proxy_busy_buffers_size 64k;
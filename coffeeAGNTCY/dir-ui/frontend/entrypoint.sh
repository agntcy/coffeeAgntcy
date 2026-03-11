#!/bin/sh
set -e

# Generate env.js from environment variable
cat > /usr/share/nginx/html/env.js << EOF
window.ENV = {
    API_URL: '${FRONTEND_API_URL:-}'
};
EOF

# Start nginx
exec nginx -g 'daemon off;'

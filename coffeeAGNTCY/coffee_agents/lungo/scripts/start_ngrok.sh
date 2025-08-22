#!/bin/bash

# Start ngrok and extract the public URL
ngrok http 4444 > /dev/null &
NGROK_PID=$!
sleep 5  # Wait for ngrok to initialize

# Get the public URL from ngrok's API
NGROK_URL=$(curl -s http://127.0.0.1:4040/api/tunnels | jq -r '.tunnels[0].public_url')

if [ -z "$NGROK_URL" ]; then
  echo "Failed to retrieve ngrok URL"
  kill $NGROK_PID
  exit 1
fi

echo "Ngrok public URL: $NGROK_URL"

# Update the IDP_ISSUER_URL in docker-compose.yaml
sed -i '' "s|IDP_ISSUER_URL=.*|IDP_ISSUER_URL=$NGROK_URL|" ./docker-compose.identity-oss.yaml

# Update the idp_url in register_issuer.py
sed -i '' "s|idp_url = .*|idp_url = \"$NGROK_URL\"|" ./scripts/register_issuer.py

# Update the urls.self.issuer field in hydra.yml
sed -i '' "s|issuer: .*|issuer: $NGROK_URL|" ./config/hydra/hydra.yml

# Stop ngrok (optional if you want it to run in the background)
#kill $NGROK_PID
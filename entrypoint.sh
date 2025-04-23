cat > entrypoint.sh << 'EOF'
#!/usr/bin/env bash
set -e

# background sync every hour
while true; do
  python sync_xm_to_spotify.py
  sleep 3600
done &

# foreground HTTP server on $PORT for health checks
exec python -m http.server "\${PORT:-8080}"
EOF

chmod +x entrypoint.sh

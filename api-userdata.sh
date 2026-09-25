#!/bin/bash
# Partner pricing API stub (runs in the partner VPC behind an internal NLB).
# systemd unit so the API survives cloud-init finishing and restarts if it dies.
cat > /root/quote.json <<'J'
{"partner":"SwiftRe","product":"motor","monthlyPremium":812.50,"currency":"ZAR"}
J

cat > /usr/local/bin/pricing-api.py <<'PY'
import http.server, socketserver

class H(http.server.BaseHTTPRequestHandler):
    def do_GET(s):
        s.send_response(200)
        s.send_header('Content-Type', 'application/json')
        s.end_headers()
        s.wfile.write(open('/root/quote.json', 'rb').read())

socketserver.TCPServer(('', 80), H).serve_forever()
PY

cat > /etc/systemd/system/pricing-api.service <<'UNIT'
[Unit]
Description=Partner pricing API
After=network.target

[Service]
ExecStart=/usr/bin/python3 /usr/local/bin/pricing-api.py
Restart=always

[Install]
WantedBy=multi-user.target
UNIT

systemctl daemon-reload
systemctl enable --now pricing-api

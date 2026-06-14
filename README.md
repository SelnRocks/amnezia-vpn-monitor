A lightweight, secure, and fast web-based monitoring dashboard for AmneziaVPN (AmneziaWG protocol) servers. This panel connects directly to your Docker containers, fetches live network stats from the Linux kernel, and displays client activity in a clean, auto-updating web interface.

## Features

- **Multi-Protocol Support:** Simultaneously monitors both `amnezia-awg` (Legacy) and `amnezia-awg2` (Modern) containers.
- **Kernel-Level Accuracy:** Bandwidth usage (Downloaded/Uploaded) and latest handshake times are parsed directly from live `wg show` outputs in real-time.
- **Dynamic Live Sorting:** Click on any table header (Protocol, Name, IP, Handshake, Traffic, Creation Date) to instantly sort rows. The layout smoothly handles natural sorting for IP addresses (`.2` comes before `.10`) and human-readable traffic units (`MiB`, `GiB`).
- **Seamless Auto-Updates:** The panel silently refreshes data every 10 seconds in the background via AJAX (Fetch API) without reloading the page or losing your chosen sort focus.
- **Secure Architecture:** Built entirely without local private key storage to prevent credential leakage. Templates are strictly protected against Server-Side Template Injection (SSTI/RCE) vulnerabilities.

## Requirements

The panel requires **Python 3.x** and **Flask** to run its web server.

- **Flask** (handles the backend server, API endpoints, routing, and Jinja2 safe templating)
- **Docker** (with running `amnezia-awg` and/or `amnezia-awg2` containers on the host)

## Installation & Running

1. Clone or upload the project files to your server.
2. Install Flask using pip:
   ```bash
   pip install flask
   ```
3. Run the monitoring server:
   ```bash
   python3 amneziamonitor.py
   ```
4. Access the dashboard in your browser at `http://YOUR_SERVER_IP:5005`.

## Production Note
For public network deployments, it is highly recommended to bind the app to `127.0.0.1` and proxy requests through Nginx configured with Basic HTTP Authentication.

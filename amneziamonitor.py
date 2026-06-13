import subprocess
import json
import traceback
import re
import os
from datetime import datetime
from flask import Flask, jsonify, request

app = Flask(__name__)
app.secret_key = os.environ.get('FLASK_SECRET_KEY', 'amnezia_secret_key_for_server_name')

HTML_TEMPLATE = r"""
<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <title>AmneziaVPN Monitor</title>
    <style>
        body { font-family: 'Segoe UI', Arial, sans-serif; margin: 20px; background-color: #f4f6f9; color: #333; }
        .container { max-width: 100%; margin: 0 auto; }
        h1 { color: #2c3e50; font-size: 24px; border-bottom: 2px solid #3498db; padding-bottom: 10px; margin-bottom: 15px; }
        .server-status-box { background: white; padding: 15px 20px; border-radius: 8px; box-shadow: 0 2px 5px rgba(0,0,0,0.05); margin-bottom: 25px; font-size: 14px; color: #2c3e50; }
        .server-status-box strong { color: #3498db; }
        table { width: 100%; border-collapse: collapse; background: white; border-radius: 8px; overflow: hidden; box-shadow: 0 4px 10px rgba(0,0,0,0.05); font-size: 13px; }
        th, td { padding: 12px 14px; text-align: left; border-bottom: 1px solid #edf2f7; vertical-align: top; }
        th { background-color: #2c3e50; color: white; text-transform: uppercase; font-size: 11px; letter-spacing: 0.8px; font-weight: 600; cursor: pointer; user-select: none; }
        th:hover { background-color: #34495e; }
        tr:hover { background-color: #f8fafc; }
        .client-name { font-size: 15px; color: #2c3e50; font-weight: 600; }
        .ip { font-family: monospace; font-weight: bold; color: #2c3e50; font-size: 13px; }
        .date { color: #7f8c8d; font-weight: 500; font-family: monospace; font-size: 13px; }
        .handshake-time { font-weight: 500; color: #2c3e50; font-family: monospace; font-size: 13px; }
        .traffic-val { font-weight: bold; font-family: monospace; color: #2c3e50; }
        .proto-badge { display: inline-block; padding: 3px 6px; border-radius: 4px; font-size: 10px; font-weight: bold; font-family: monospace; white-space: nowrap; }
        .proto-awg { background-color: #e3f2fd; color: #0d47a1; }
        .proto-awg2 { background-color: #f3e5f5; color: #4a148c; }
        .sort-indicator { margin-left: 4px; opacity: 0.6; font-size: 10px; }
    </style>
</head>
    {% raw %}
    <script>
        let currentSortCol = "date"; 
        let currentSortDir = "desc"; 

        function handleHeaderClick(sortField) {
            if (currentSortCol === sortField) {
                currentSortDir = currentSortDir === "asc" ? "desc" : "asc";
            } else {
                currentSortCol = sortField;
                currentSortDir = "asc";
            }
            updateData(); 
        }

        async function updateData() {
            try {
                let response = await fetch(`/api/clients?sort_by=${currentSortCol}&sort_dir=${currentSortDir}`);
                if (!response.ok) return;
                let clients = await response.json();
                
                let tableBody = document.getElementById("vpnBody");
                if (!tableBody) return;
                tableBody.innerHTML = "";

                clients.forEach((client, idx) => {
                    let row = document.createElement("tr");
                    let badge = client.protocol === 'amnezia-awg' ? 
                        `<span class="proto-badge proto-awg">AWG</span>` : 
                        `<span class="proto-badge proto-awg2">AWG-2</span>`;

                    row.innerHTML = `
                        <td>${idx + 1}</td>
                        <td>${badge}</td>
                        <td><span class="client-name">${client.name}</span></td>
                        <td><span class="ip">${client.allowed_ips}</span></td>
                        <td><span class="handshake-time">${client.final_handshake}</span></td>
                        <td><span class="traffic-val">${client.final_sent}</span></td>
                        <td><span class="traffic-val">${client.final_received}</span></td>
                        <td><span class="date">${client.creation_date}</span></td>
                    `;
                    tableBody.appendChild(row);
                });

                let headers = document.querySelectorAll("#vpnHeader th");
                headers.forEach(th => {
                    let indicator = th.querySelector('.sort-indicator');
                    if (indicator) {
                        if (th.getAttribute("data-field") === currentSortCol) {
                            indicator.innerText = currentSortDir === "asc" ? " ▲" : " ▼";
                        } else {
                            indicator.innerText = " ↕";
                        }
                    }
                });

            } catch (err) {
                console.error("Data update error:", err);
            }
        }

        setInterval(updateData, 10000);
    </script>
    {% endraw %}
</head>

<body>
    <div class="container">
        <h1>AmneziaVPN Clients Monitor</h1>

        <table>
            <thead id="vpnHeader">
                <tr>
                    <th style="width: 3%">#</th>
                    <th style="width: 8%" data-field="protocol" onclick="handleHeaderClick('protocol')">Protocol<span class="sort-indicator"> ↕</span></th>
                    <th style="width: 20%" data-field="name" onclick="handleHeaderClick('name')">Client Name<span class="sort-indicator"> ↕</span></th>
                    <th style="width: 11%" data-field="ip" onclick="handleHeaderClick('ip')">IP<span class="sort-indicator"> ↕</span></th>
                    <th style="width: 24%" data-field="handshake" onclick="handleHeaderClick('handshake')">Handshake<span class="sort-indicator"> ↕</span></th>
                    <th style="width: 12%" data-field="sent" onclick="handleHeaderClick('sent')">Download<span class="sort-indicator"> ↕</span></th>
                    <th style="width: 12%" data-field="received" onclick="handleHeaderClick('received')">Upload<span class="sort-indicator"> ↕</span></th>
                    <th style="width: 10%" data-field="date" onclick="handleHeaderClick('date')">Create Date<span class="sort-indicator"> ▲</span></th>
                </tr>
            </thead>
            <tbody id="vpnBody">
                {% for client in clients %}
                <tr>
                    <td>{{ loop.index }}</td>
                    <td>
                        {% if client.protocol == 'amnezia-awg' %}
                            <span class="proto-badge proto-awg">AWG</span>
                        {% else %}
                            <span class="proto-badge proto-awg2">AWG-2</span>
                        {% endif %}
                    </td>
                    <td><span class="client-name">{{ client.name }}</span></td>
                    <td><span class="ip">{{ client.allowed_ips }}</span></td>
                    <td><span class="handshake-time">{{ client.final_handshake }}</span></td>
                    <td><span class="traffic-val">{{ client.final_sent }}</span></td>
                    <td><span class="traffic-val">{{ client.final_received }}</span></td>
                    <td><span class="date">{{ client.creation_date }}</span></td>
                </tr>
                {% endfor %}
            </tbody>
        </table>
    </div>
</body>
</html>
"""

def clean_date_string(date_str):
    if not date_str or date_str == "-": 
        return "-"
    date_str = str(date_str).replace("T", " ")
    if "." in date_str: 
        date_str = date_str.split(".")
    return date_str.strip()

def format_creation_date(raw_date):
    cleaned = clean_date_string(raw_date)
    if cleaned == "-": 
        return "-"
    
    months_map = {
        "jan": "01", "feb": "02", "mar": "03", "apr": "04", "may": "05", "jun": "06",
        "jul": "07", "aug": "08", "sep": "09", "oct": "10", "nov": "11", "dec": "12"
    }
    
    try:
        dt = datetime.strptime(cleaned, "%Y-%m-%d %H:%M:%S")
        return dt.strftime("%d.%m.%Y %H:%M:%S")
    except ValueError:
        pass

    match = re.match(r"^[A-Za-z]+\s+([A-Za-z]+)\s+(\d+)\s+(\d{2}:\d{2}:\d{2})\s+(\d{4})", cleaned)
    if match:
        month_str, day_str, time_str, year_str = match.groups()
        month_num = months_map.get(month_str.lower(), "01")
        day_num = day_str.zfill(2)
        return f"{day_num}.{month_num}.{year_str} {time_str}"
        
    return raw_date

def traffic_to_bytes(traffic_str):
    if not traffic_str or traffic_str in ["0 B", "-", "No data"]:
        return 0
    try:
        match = re.match(r"^([\d.]+)\s*([A-Za-z]*)$", traffic_str.strip())
        if not match:
            return 0
        value, unit = match.groups()
        value = float(value)
        unit = unit.lower()
        
        multipliers = {
            'b': 1, 'kib': 1024, 'mib': 1024 ** 2, 'gib': 1024 ** 3, 'tib': 1024 ** 4,
            'kb': 1000, 'mb': 1000 ** 2, 'gb': 1000 ** 3
        }
        return int(value * multipliers.get(unit, 1))
    except Exception:
        return 0

def handshake_to_seconds(hs_str):
    if not hs_str or any(x in hs_str for x in ["Never", "No data", "Never"]):
        return 9999999999
    try:
        total_seconds = 0
        hs_str = hs_str.lower()
        
        days = re.search(r"(\d+)\s*day", hs_str)
        hours = re.search(r"(\d+)\s*hour", hs_str)
        minutes = re.search(r"(\d+)\s*min", hs_str)
        short_mins = re.search(r"(\d+)\s*m\s+ago", hs_str)
        seconds = re.search(r"(\d+)\s*sec", hs_str)
        
        if days: total_seconds += int(days.group(1)) * 86400
        if hours: total_seconds += int(hours.group(1)) * 3600
        if minutes: total_seconds += int(minutes.group(1)) * 60
        elif short_mins: total_seconds += int(short_mins.group(1)) * 60
        if seconds: total_seconds += int(seconds.group(1))
        
        return total_seconds if total_seconds > 0 else 9999999998
    except Exception:
        return 9999999999

def date_to_timestamp(date_str):
    if not date_str or date_str == "-":
        return 0
    try:
        dt = datetime.strptime(date_str, "%d.%m.%Y %H:%M:%S")
        return int(dt.timestamp())
    except Exception:
        return 0

def ip_sort_key(ip_str):
    try:
        return [int(x) for x in ip_str.split('.')]
    except Exception:
        return [0, 0, 0, 0]

def parse_wg_live(container_name):
    live_data = {}
    try:
        cmd = ["docker", "exec", container_name, "wg", "show"]
        result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, timeout=5)
        if result.returncode != 0 or not result.stdout.strip(): 
            return live_data
        output = result.stdout
    except Exception: 
        return live_data

    peers = re.findall(r"peer:\s+(\S+)(.*?)(?=peer:|$)", output, re.DOTALL)
    for peer_key, peer_body in peers:
        handshake, rcv, snt, ips = "Never connected", "0 B", "0 B", "-"
        for line in peer_body.strip().splitlines():
            line = line.strip()
            if line.startswith("allowed ips:"): 
                ips = line.split(":", 1)[1].strip()
            elif line.startswith("latest handshake:"): 
                handshake = line.split(":", 1)[1].strip()
            elif line.startswith("transfer:"):
                t_str = line.split(":", 1)[1].strip()
                parts = t_str.split(",")
                if len(parts) == 2:
                    rcv = parts[0].replace("received", "").strip()
                    snt = parts[1].replace("sent", "").strip()
        live_data[peer_key.strip()] = {
            "handshake": handshake, 
            "received": rcv, 
            "sent": snt, 
            "allowed_ips": ips
        }
    return live_data

def get_all_amnezia_parameters(sort_by="date", sort_dir="desc"):
    all_clients = []
    containers = ["amnezia-awg", "amnezia-awg2"]

    for container in containers:
        live_wg = parse_wg_live(container)
        if not live_wg:
            continue

        names_map = {}
        creation_dates_map = {}
        try:
            res = subprocess.run(
                ["docker", "exec", container, "cat", "/opt/amnezia/awg/clientsTable"],
                stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, timeout=5
            )
            if res.returncode == 0:
                json_data = json.loads(res.stdout.replace("\r", ""))
                for item in json_data:
                    p_key = item.get("clientId", "").strip()
                    if p_key:
                        u_data = item.get("userData", {})
                        names_map[p_key] = u_data.get("clientName", "No name")
                        creation_dates_map[p_key] = u_data.get("creationDate", "-")
        except Exception:
            pass

        for peer_key, live_info in live_wg.items():
            try:
                client_name = names_map.get(peer_key, f"Unknown ({peer_key[:8]})")
                creation_date_raw = creation_dates_map.get(peer_key, "-")
                
                raw_ip = live_info.get("allowed_ips", "-")
                clean_ip = raw_ip.replace("/32", "").strip()
                
                final_hs = live_info.get("handshake", "Нет данных")
                final_received = live_info.get("received", "0 B")
                final_sent = live_info.get("sent", "0 B")
                formatted_date = format_creation_date(creation_date_raw)

                all_clients.append({
                    "protocol": container,
                    "name": client_name,
                    "allowed_ips": clean_ip,
                    "creation_date": formatted_date,
                    "final_received": final_received,
                    "final_sent": final_sent,
                    "final_handshake": final_hs,
                    "_received_bytes": traffic_to_bytes(final_received),
                    "_sent_bytes": traffic_to_bytes(final_sent),
                    "_handshake_seconds": handshake_to_seconds(final_hs),
                    "_date_timestamp": date_to_timestamp(formatted_date),
                    "_ip_key": ip_sort_key(clean_ip)
                })
            except Exception:
                continue

    is_reverse = (sort_dir == "desc")
    
    if sort_by == "name":
        all_clients.sort(key=lambda x: x["name"].lower(), reverse=is_reverse)
    elif sort_by == "protocol":
        all_clients.sort(key=lambda x: x["protocol"], reverse=is_reverse)
    elif sort_by == "ip":
        all_clients.sort(key=lambda x: x["_ip_key"], reverse=is_reverse)
    elif sort_by == "handshake":
        all_clients.sort(key=lambda x: x["_handshake_seconds"], reverse=is_reverse)
    elif sort_by == "received":
        all_clients.sort(key=lambda x: x["_received_bytes"], reverse=is_reverse)
    elif sort_by == "sent":
        all_clients.sort(key=lambda x: x["_sent_bytes"], reverse=is_reverse)
    else: # По умолчанию: date
        all_clients.sort(key=lambda x: x["_date_timestamp"], reverse=is_reverse)

    return all_clients

@app.route('/')
def index():
    try:
        clients = get_all_amnezia_parameters(sort_by="date", sort_dir="desc")
        from jinja2 import Template
        tmpl = Template(HTML_TEMPLATE)
        return tmpl.render(clients=clients)
    except Exception as e:
        return f"<pre>Server error:\n{traceback.format_exc()}</pre>", 500

@app.route('/api/clients')
def api_clients():
    try:
        sort_by = request.args.get('sort_by', 'date')
        sort_dir = request.args.get('sort_dir', 'desc')
        clients = get_all_amnezia_parameters(sort_by=sort_by, sort_dir=sort_dir)
        return jsonify(clients)
    except Exception:
        return jsonify([]), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5005)

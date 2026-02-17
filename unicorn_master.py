"""
Smart Unicorn Master - Puma-style auto configuration
One app file + config = automatic multi-worker deployment
"""

import subprocess
import time
import os
import json
import sys

os.environ['PYTHONIOENCODING'] = 'utf-8'

VENV_PYTHON = "C:/production/venv/Scripts/python.exe"
CONFIG_FILE = "C:/production/unicorn_config.json"

def log(msg):
    print(f"[{time.strftime('%H:%M:%S')}] {msg}", flush=True)

def load_config():
    with open(CONFIG_FILE, 'r') as f:
        return json.load(f)

def build_workers(config):
    """
    Automatically build worker list from config
    Like Puma reading its config file
    """
    workers = []

    for service in config['services']:
        name = service['name']
        script = service['script']
        worker_count = service['workers']
        threads = service['threads']
        start_port = service['start_port']

        log(f"Service: {name} -> {worker_count} workers x {threads} threads")

        for i in range(worker_count):
            port = start_port + i
            instance_name = f"{name.capitalize()}-Worker{i+1}"

            workers.append({
                'id': f"{name}_worker{i+1}",
                'service': name,
                'instance_name': instance_name,
                'port': port,
                'script': script,
                'threads': threads,
                'process': None,
                'pid': None,
                'restarts': 0
            })

    return workers

def start_worker(worker):
    """Start a single worker"""
    env = os.environ.copy()
    env['INSTANCE_NAME'] = worker['instance_name']
    env['INSTANCE_PORT'] = str(worker['port'])
    env['WORKER_THREADS'] = str(worker['threads'])
    env['PYTHONIOENCODING'] = 'utf-8'

    try:
        process = subprocess.Popen(
            [VENV_PYTHON, worker['script']],
            env=env,
            cwd=os.path.dirname(worker['script']),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        worker['process'] = process
        worker['pid'] = process.pid
        log(f"  Started {worker['instance_name']} on port {worker['port']} (PID: {process.pid})")
        return True
    except Exception as e:
        log(f"  ERROR starting {worker['instance_name']}: {e}")
        return False

def check_worker(worker):
    """Check if worker is alive"""
    if worker['process'] is None:
        return False
    return worker['process'].poll() is None

def restart_worker(worker):
    """Restart a dead worker"""
    log(f"Restarting {worker['instance_name']}...")
    worker['restarts'] += 1

    # Kill old process if still exists
    try:
        if worker['process']:
            worker['process'].terminate()
    except:
        pass

    time.sleep(2)
    return start_worker(worker)

def generate_nginx_config(workers, config):
    """
    Auto-generate Nginx config from workers
    No manual Nginx editing needed!
    """
    upstreams = {}
    for service in config['services']:
        name = service['name']
        upstreams[name] = []

    for worker in workers:
        service = worker['service']
        upstreams[service].append(worker['port'])

    nginx_config = "worker_processes  auto;\n\nevents {\n    worker_connections  1024;\n}\n\nhttp {\n    include       mime.types;\n    default_type  application/json;\n    sendfile        on;\n    keepalive_timeout  65;\n\n"

    # Upstream blocks
    for service, ports in upstreams.items():
        nginx_config += f"    upstream {service}_backend {{\n"
        nginx_config += "        least_conn;\n"
        for port in ports:
            nginx_config += f"        server 127.0.0.1:{port} max_fails=3 fail_timeout=30s;\n"
        nginx_config += "        keepalive 32;\n"
        nginx_config += "    }\n\n"

    # Server block
    nginx_config += "    server {\n"
    nginx_config += "        listen 0.0.0.0:80;\n"
    nginx_config += "        server_name _;\n\n"

    nginx_config += """        location /test {
            alias C:/production/static/;
            index thread_test.html;
        }\n\n"""

    for service in upstreams.keys():
        if service == 'users':
            nginx_config += f"""        location /api/auth {{
            proxy_pass http://{service}_backend;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_http_version 1.1;
            proxy_set_header Connection "";
        }}\n\n"""
            nginx_config += f"""        location /api/users {{
            proxy_pass http://{service}_backend;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_http_version 1.1;
            proxy_set_header Connection "";
        }}\n\n"""
        else:
            nginx_config += f"""        location /api/{service} {{
            proxy_pass http://{service}_backend;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_http_version 1.1;
            proxy_set_header Connection "";
        }}\n\n"""

    nginx_config += """        location / {
            return 200 '{"api":"E-Commerce API","status":"running"}';
            add_header Content-Type application/json;
        }
    }
}\n"""

    # Write nginx config
    nginx_path = "C:/nginx/conf/nginx.conf"
    with open(nginx_path, 'w') as f:
        f.write(nginx_config)

    log(f"Nginx config auto-generated: {nginx_path}")

def print_status(workers, config):
    """Print current status"""
    print("\n" + "=" * 70)
    print("WORKER STATUS")
    print("=" * 70)

    for service in config['services']:
        name = service['name']
        service_workers = [w for w in workers if w['service'] == name]
        alive = sum(1 for w in service_workers if check_worker(w))
        total_threads = service['workers'] * service['threads']

        print(f"\n  {name.upper()} SERVICE")
        print(f"  Workers: {alive}/{len(service_workers)} alive")
        print(f"  Threads: {total_threads} total ({service['threads']} per worker)")

        for w in service_workers:
            status = "RUNNING" if check_worker(w) else "DEAD"
            print(f"    [{status}] {w['instance_name']} -> Port {w['port']} (PID: {w['pid']}, Restarts: {w['restarts']})")

    print("\n" + "=" * 70)
    print("ACCESS URLS")
    print("=" * 70)
    print("  Products: http://localhost/api/products")
    print("  Orders:   http://localhost/api/orders")
    print("  Auth:     http://localhost/api/auth/login")
    print("  Test:     http://localhost/test")
    print("=" * 70 + "\n")

def main():
    print("=" * 70)
    print("UNICORN MASTER - PUMA-STYLE AUTO CONFIGURATION")
    print("=" * 70)
    print(f"Python: {VENV_PYTHON}")
    print(f"Config: {CONFIG_FILE}")
    print("=" * 70)

    # Load config
    config = load_config()
    log(f"Loaded {len(config['services'])} services")

    # Auto-build worker list from config
    log("Building workers from config...")
    workers = build_workers(config)
    log(f"Total workers to spawn: {len(workers)}")

    # Auto-generate Nginx config
    log("Generating Nginx config...")
    generate_nginx_config(workers, config)

    # Reload Nginx
    log("Reloading Nginx...")
    os.system("C:\\nginx\\nginx.exe -s reload")

    # Start all workers
    print("\n" + "=" * 70)
    log("Starting all workers...")
    print("=" * 70)

    for worker in workers:
        start_worker(worker)
        time.sleep(2)

    # Wait for initialization
    log("Waiting for workers to initialize...")
    time.sleep(10)

    # Print status
    print_status(workers, config)

    # Monitor loop
    log("Starting monitoring loop (checks every 15 seconds)...")
    check_count = 0

    try:
        while True:
            time.sleep(15)
            check_count += 1

            any_dead = False
            for worker in workers:
                if not check_worker(worker):
                    any_dead = True
                    log(f"Worker {worker['instance_name']} died! Restarting...")
                    restart_worker(worker)

            if check_count % 4 == 0:  # Print status every minute
                print_status(workers, config)

    except KeyboardInterrupt:
        log("Shutting down all workers...")
        for worker in workers:
            try:
                if worker['process']:
                    worker['process'].terminate()
                    log(f"Stopped {worker['instance_name']}")
            except:
                pass
        log("Shutdown complete")
        sys.exit(0)

if __name__ == "__main__":
    main()
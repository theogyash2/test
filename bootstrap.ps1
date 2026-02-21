# ONE-CLICK SERVER SETUP
# Run this on ANY fresh Windows instance

Write-Host "Setting up production server..." -ForegroundColor Green

# Install dependencies
Write-Host "Installing Python..." -ForegroundColor Cyan
winget install Python.Python.3.13 -e --silent

# Install Git
Write-Host "Installing Git..." -ForegroundColor Cyan
winget install Git.Git -e --silent

# Clone repo
Write-Host "Cloning repository..." -ForegroundColor Cyan
git clone https://github.com/theogyash2/test.git C:\production
cd C:\production

# Setup Python
Write-Host "Setting up Python environment..." -ForegroundColor Cyan
python -m venv venv
.\venv\Scripts\pip.exe install -r requirements.txt

# Initialize database
Write-Host "Initializing database..." -ForegroundColor Cyan
.\venv\Scripts\python.exe init_database.py

# Install services
Write-Host "Installing services..." -ForegroundColor Cyan

# Download NSSM
Invoke-WebRequest -Uri "https://nssm.cc/release/nssm-2.24.zip" -OutFile "nssm.zip"
Expand-Archive nssm.zip -DestinationPath .

# Install Unicorn Master service
.\nssm\nssm-2.24\win64\nssm.exe install UnicornMaster "C:\production\venv\Scripts\python.exe" "C:\production\unicorn_master.py"
.\nssm\nssm-2.24\win64\nssm.exe set UnicornMaster AppDirectory "C:\production"
.\nssm\nssm-2.24\win64\nssm.exe set UnicornMaster Start SERVICE_AUTO_START

# Install Webhook service
.\nssm\nssm-2.24\win64\nssm.exe install WebhookListener "C:\production\venv\Scripts\python.exe" "C:\production\webhook_listener.py"
.\nssm\nssm-2.24\win64\nssm.exe set WebhookListener AppDirectory "C:\production"
.\nssm\nssm-2.24\win64\nssm.exe set WebhookListener Start SERVICE_AUTO_START

# Install Nginx
Write-Host "Installing Nginx..." -ForegroundColor Cyan
Invoke-WebRequest -Uri "http://nginx.org/download/nginx-1.24.0.zip" -OutFile "nginx.zip"
Expand-Archive nginx.zip -DestinationPath C:\
Rename-Item C:\nginx-1.24.0 C:\nginx

# Copy nginx config
Copy-Item nginx.conf C:\nginx\conf\nginx.conf

# Install Nginx service
C:\production\nssm\nssm-2.24\win64\nssm.exe install NginxService "C:\nginx\nginx.exe"
C:\production\nssm\nssm-2.24\win64\nssm.exe set NginxService AppDirectory "C:\nginx"
C:\production\nssm\nssm-2.24\win64\nssm.exe set NginxService Start SERVICE_AUTO_START

# Open firewall ports
Write-Host "Opening firewall ports..." -ForegroundColor Cyan
New-NetFirewallRule -DisplayName "HTTP" -Direction Inbound -LocalPort 80 -Protocol TCP -Action Allow
New-NetFirewallRule -DisplayName "Webhook" -Direction Inbound -LocalPort 9000 -Protocol TCP -Action Allow

# Start services
Write-Host "Starting services..." -ForegroundColor Cyan
.\nssm\nssm-2.24\win64\nssm.exe start UnicornMaster
.\nssm\nssm-2.24\win64\nssm.exe start WebhookListener
.\nssm\nssm-2.24\win64\nssm.exe start NginxService

Write-Host "`n========================================" -ForegroundColor Green
Write-Host "SETUP COMPLETE!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host "API running on: http://YOUR_IP" -ForegroundColor Yellow
Write-Host "Webhook URL: http://YOUR_IP:9000/deploy" -ForegroundColor Yellow
Write-Host "`nGo to GitHub and add webhook URL!" -ForegroundColor Cyan
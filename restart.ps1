Write-Host "Restarting workers..." -ForegroundColor Cyan
C:\production\nssm\nssm-2.24\win64\nssm.exe restart UnicornMaster
Start-Sleep -Seconds 15
curl http://localhost/api/products -UseBasicParsing
Write-Host "Done!" -ForegroundColor Green
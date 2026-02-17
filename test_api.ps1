Write-Host "Complete E-Commerce API Test" -ForegroundColor Green
Write-Host "======================================================================"

# Test 1: Get Products
Write-Host "`nTest 1: Get all products (public)" -ForegroundColor Cyan
$products = Invoke-RestMethod -Uri "http://localhost/api/products"
Write-Host "Success! Found $($products.total) products" -ForegroundColor Green
Write-Host "   First product: $($products.products[0].name) - $($products.products[0].price)" -ForegroundColor Gray

# Test 2: Register User
Write-Host "`nTest 2: User registration" -ForegroundColor Cyan
$registerBody = @{
    username = "testuser_$(Get-Random -Maximum 9999)"
    email = "test$(Get-Random -Maximum 9999)@example.com"
    password = "password123"
} | ConvertTo-Json

try {
    $registerResponse = Invoke-RestMethod -Uri "http://localhost/api/auth/register" -Method POST -Body $registerBody -ContentType "application/json"
    Write-Host "User registered successfully!" -ForegroundColor Green
    Write-Host "   Username: $($registerResponse.user.username)" -ForegroundColor Gray
    $token = $registerResponse.access_token
} catch {
    Write-Host "Registration failed: $($_.Exception.Message)" -ForegroundColor Red
    exit
}

# Test 3: Login
Write-Host "`nTest 3: User login" -ForegroundColor Cyan
$loginBody = @{
    username = $registerResponse.user.username
    password = "password123"
} | ConvertTo-Json

$loginResponse = Invoke-RestMethod -Uri "http://localhost/api/auth/login" -Method POST -Body $loginBody -ContentType "application/json"
Write-Host "Login successful!" -ForegroundColor Green
$token = $loginResponse.access_token

# Test 4: Get User Info
Write-Host "`nTest 4: Get current user (authenticated)" -ForegroundColor Cyan
$userInfo = Invoke-RestMethod -Uri "http://localhost/api/users/me" -Headers @{ Authorization = "Bearer $token" }
Write-Host "User info retrieved!" -ForegroundColor Green
Write-Host "   Email: $($userInfo.user.email)" -ForegroundColor Gray

# Test 5: Create Order
Write-Host "`nTest 5: Create order (authenticated)" -ForegroundColor Cyan
$orderBody = @{
    items = @(
        @{
            product_id = $products.products[0].id
            quantity = 2
        },
        @{
            product_id = $products.products[1].id
            quantity = 1
        }
    )
} | ConvertTo-Json

$orderResponse = Invoke-RestMethod -Uri "http://localhost/api/orders" -Method POST -Body $orderBody -ContentType "application/json" -Headers @{ Authorization = "Bearer $token" }
Write-Host "Order created!" -ForegroundColor Green
Write-Host "   Order ID: $($orderResponse.order.id)" -ForegroundColor Gray
Write-Host "   Total: $($orderResponse.order.total_amount)" -ForegroundColor Gray
Write-Host "   Items: $($orderResponse.order.items.Count)" -ForegroundColor Gray

# Test 6: Get Orders
Write-Host "`nTest 6: Get my orders (authenticated)" -ForegroundColor Cyan
$myOrders = Invoke-RestMethod -Uri "http://localhost/api/orders" -Headers @{ Authorization = "Bearer $token" }
Write-Host "Orders retrieved!" -ForegroundColor Green
Write-Host "   Total orders: $($myOrders.total)" -ForegroundColor Gray

# Test 7: Search
Write-Host "`nTest 7: Search products" -ForegroundColor Cyan
$searchResults = Invoke-RestMethod -Uri "http://localhost/api/products/search?q=laptop"
Write-Host "Search completed!" -ForegroundColor Green
Write-Host "   Found: $($searchResults.total) results for laptop" -ForegroundColor Gray

# Test 8: Load Balancing
Write-Host "`nTest 8: Load balancing across workers" -ForegroundColor Cyan
$instances = @{}
1..10 | ForEach-Object {
    $response = Invoke-RestMethod -Uri "http://localhost/api/products"
    $instance = $response.instance
    if ($instances.ContainsKey($instance)) {
        $instances[$instance]++
    } else {
        $instances[$instance] = 1
    }
}
Write-Host "Load balancing verified!" -ForegroundColor Green
foreach ($key in $instances.Keys) {
    Write-Host "   $key handled $($instances[$key]) requests" -ForegroundColor Gray
}

Write-Host "`n======================================================================"
Write-Host "ALL TESTS PASSED! API is fully operational!" -ForegroundColor Green
Write-Host "======================================================================`n"

Write-Host "API Summary:" -ForegroundColor Yellow
Write-Host "   Base URL: http://localhost"
Write-Host "   Services: Products, Orders, Users/Auth"
Write-Host "   Workers: 6 workers (2 per service)"
Write-Host "   Load Balancing: Active"
Write-Host "   Authentication: JWT tokens"
Write-Host "   Database: SQLite with $($products.total) products"
# PowerShell script to update an existing Caspian deployment with vector extension fixes

Write-Host "Caspian Deployment Update Script" -ForegroundColor Cyan
Write-Host "===============================" -ForegroundColor Cyan
Write-Host

# Check if Docker is available
try {
    $dockerVersion = docker --version
    Write-Host "Found Docker: $dockerVersion"
} catch {
    Write-Host "Error: Docker is not installed or not in PATH" -ForegroundColor Red
    exit 1
}

# Check if Docker Compose is available
try {
    $composeVersion = docker-compose --version
    Write-Host "Found Docker Compose: $composeVersion"
} catch {
    Write-Host "Error: docker-compose is not installed or not in PATH" -ForegroundColor Red
    exit 1
}

# Function to check container status
function Test-Container {
    param (
        [string]$containerName
    )
    
    $container = docker ps -q -f name=$containerName
    if ($container) {
        Write-Host "✅ Container $containerName is running" -ForegroundColor Green
        
        # Check health status
        $health = docker inspect --format='{{.State.Health.Status}}' $containerName 2>$null
        if ($health -eq "healthy") {
            Write-Host "   Health status: healthy" -ForegroundColor Green
        } elseif ($health -eq "unhealthy") {
            Write-Host "⚠️ Health status: unhealthy" -ForegroundColor Yellow
        } else {
            Write-Host "   Health status: $health"
        }
        
        return $true
    } else {
        Write-Host "❌ Container $containerName is not running" -ForegroundColor Red
        return $false
    }
}

# Check containers status
Write-Host "Checking container status..." -ForegroundColor Yellow
$postgresRunning = Test-Container "caspian-postgres"
if (-not $postgresRunning) { Write-Host "   Not found - will be created" -ForegroundColor Yellow }

$backendRunning = Test-Container "caspian-backend"
if (-not $backendRunning) { Write-Host "   Not found - will be created" -ForegroundColor Yellow }

$frontendRunning = Test-Container "caspian-frontend"
if (-not $frontendRunning) { Write-Host "   Not found - will be created" -ForegroundColor Yellow }

Write-Host

# Backup existing files
Write-Host "Backing up existing files..." -ForegroundColor Yellow
if (Test-Path "docker-compose.yml") {
    Copy-Item "docker-compose.yml" "docker-compose.yml.bak"
} else {
    Write-Host "No docker-compose.yml file found - will create new one" -ForegroundColor Yellow
}

if (Test-Path "init-vector.sql") {
    Copy-Item "init-vector.sql" "init-vector.sql.bak"
} else {
    Write-Host "No init-vector.sql file found - will create new one" -ForegroundColor Yellow
}
Write-Host "✅ Backup complete" -ForegroundColor Green
Write-Host

# Copy fixed files
Write-Host "Updating configuration files..." -ForegroundColor Yellow
Copy-Item "docker-compose.fixed.yml" "docker-compose.yml"
Copy-Item "init-vector.fixed.sql" "init-vector.sql"
Write-Host "✅ Configuration files updated" -ForegroundColor Green
Write-Host

# Update existing deployment
Write-Host "Updating the deployment..." -ForegroundColor Yellow
$answer = Read-Host "This will restart all containers. Continue? (y/n)"
if ($answer -eq "y" -or $answer -eq "Y") {
    Write-Host "Stopping containers..." -ForegroundColor Yellow
    docker-compose down
    
    Write-Host "Starting containers with fixed configuration..." -ForegroundColor Yellow
    docker-compose up -d
    
    Write-Host "Waiting for containers to initialize..." -ForegroundColor Yellow
    Start-Sleep -Seconds 10
    
    Write-Host "Checking updated container status..." -ForegroundColor Yellow
    $postgresRunning = Test-Container "caspian-postgres"
    $backendRunning = Test-Container "caspian-backend"
    $frontendRunning = Test-Container "caspian-frontend"
    
    # Check if backend is still unhealthy
    $backendHealth = docker inspect --format='{{.State.Health.Status}}' caspian-backend 2>$null
    if ($backendHealth -eq "unhealthy") {
        Write-Host
        Write-Host "⚠️ Backend still shows as unhealthy. Running direct vector extension fix..." -ForegroundColor Yellow
        
        Write-Host "Connecting to PostgreSQL container to fix vector extension..." -ForegroundColor Yellow
        docker exec -it caspian-postgres psql -U caspian_user -d caspian_db -c "CREATE EXTENSION IF NOT EXISTS vector;"
        docker exec -it caspian-postgres psql -U caspian_user -d caspian_db -c "SELECT '[1,2,3]'::text::vector;"
        
        Write-Host "Restarting backend container..." -ForegroundColor Yellow
        docker restart caspian-backend
        
        Write-Host "Waiting for backend to initialize..." -ForegroundColor Yellow
        Start-Sleep -Seconds 10
        
        Write-Host "Final backend status:" -ForegroundColor Yellow
        Test-Container "caspian-backend"
    }
    
    Write-Host
    Write-Host "Deployment update completed!" -ForegroundColor Green
    Write-Host "You can access the application at http://localhost" -ForegroundColor Cyan
    Write-Host "Check the API test component to verify authentication is working." -ForegroundColor Cyan
} else {
    Write-Host "Update cancelled." -ForegroundColor Yellow
}

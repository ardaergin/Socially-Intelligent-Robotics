# Start Redis server
Write-Host "Starting Redis server..."
$redisProcess = Start-Process "redis-server" -ArgumentList "conf/redis/redis.conf" -PassThru

# Start GPT service
Write-Host "Starting GPT service..."
$gptProcess = Start-Process "run-gpt" -PassThru

# Start Whisper service
Write-Host "Starting Whisper service..."
$whisperProcess = Start-Process "run-whisper" -PassThru

# Wait a few seconds for services to start
Write-Host "Waiting for services to start..."
Start-Sleep -Seconds 5

# Run the main Python program
Write-Host "Running main Python program..."
python -m app.main

# After the Python program exits, terminate the services
Write-Host "Terminating services..."
if ($redisProcess) { Stop-Process -Id $redisProcess.Id -Force }
if ($gptProcess) { Stop-Process -Id $gptProcess.Id -Force }
if ($whisperProcess) { Stop-Process -Id $whisperProcess.Id -Force }

Write-Host "All services terminated."

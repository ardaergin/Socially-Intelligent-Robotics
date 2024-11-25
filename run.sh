#!/bin/bash
# Make the Script Executable: chmod +x run.sh

# Start Redis server
redis-server conf/redis/redis.conf &
REDIS_PID=$!

# Start GPT service
run-gpt &
GPT_PID=$!

# Start Whisper service
run-whisper &
WHISPER_PID=$!

# Wait a few seconds for services to start
sleep 5

# Run the main Python program
python -m app.main

# After the Python program exits, terminate the services
kill $REDIS_PID
kill $GPT_PID
kill $WHISPER_PID

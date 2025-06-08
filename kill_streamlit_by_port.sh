#!/bin/bash

# Port number your Streamlit app is running on
STREAMLIT_PORT=8501

echo "Attempting to kill Streamlit process on port $STREAMLIT_PORT..."

# Find the PID listening on the specified port
PID=$(sudo lsof -t -i :$STREAMLIT_PORT)

if [ -z "$PID" ]; then
    echo "No process found listening on port $STREAMLIT_PORT."
else
    echo "Found process with PID: $PID on port $STREAMLIT_PORT."
    # Attempt to gracefully kill the process
    kill $PID
    sleep 2 # Give it a moment to shut down

    # Check if the process is still running
    if ps -p $PID > /dev/null; then
        echo "Process $PID is still running. Force killing..."
        kill -9 $PID
        echo "Process $PID force killed."
    else
        echo "Process $PID gracefully terminated."
    fi
fi
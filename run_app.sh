#!/bin/bash

echo "Starting Mongo memory assistant..."
python3 -m streamlit run ui/app.py --server.port 8501 --server.address 0.0.0.0

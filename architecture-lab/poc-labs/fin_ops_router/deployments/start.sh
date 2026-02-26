#!/bin/bash
# start.sh - Launch FastAPI + Streamlit in same container

# Run FastAPI in background
uvicorn src.main:app --host 0.0.0.0 --port 8001 &

# Give FastAPI a few seconds to start
sleep 3

# Run Streamlit dashboard
streamlit run dashboards/dashboard.py --server.port 8501 --server.address 0.0.0.0

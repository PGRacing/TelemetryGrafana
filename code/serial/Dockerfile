# syntax=docker/dockerfile:1
FROM python:3.8

# Install dependencies
RUN pip install asyncio websockets

# Copy your script into the container
COPY websocket_server.py .

# Run your script when the container starts
CMD ["python", "./websocket_server.py"]
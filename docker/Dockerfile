# https://docs.docker.com/engine/reference/builder/

# Use an official Python runtime as a parent image
# See https://hub.docker.com/ and search for python:2.7-slim
FROM tiangolo/uvicorn-gunicorn-fastapi:python3.7

# Set the working directory to /app
# The WORKDIR instruction sets the working directory (inside the container) 
# for any RUN, CMD, ENTRYPOINT, COPY and ADD instructions that 
# follow it in the Dockerfile. 
WORKDIR /app

# Copy the current directory contents into the container at /app
ADD ./app /app

# Install any needed packages specified in requirements.txt
# RUN during image build
RUN pip install --trusted-host pypi.python.org -r requirements.txt
RUN apt-get update && apt-get install -y dnsutils 
# Make port 80 available to the world outside this container
EXPOSE 80
# EXPOSE 8000

# Run python app.py when the container launches
# This happens if no command is specified
# CMD ["python", "app.py"]


CMD ["gunicorn", "app:app", "-b", "0.0.0.0:80", "-w", "4", "-k", "uvicorn.workers.UvicornWorker"]
# CMD ["uvicorn", "appNew:app", "--host", "0.0.0.0", "--port", "80"]

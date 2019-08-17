# Use an official Python runtime as a parent image
FROM python:2.7

# Set the working directory to /app
WORKDIR /app

# Copy the current directory contents into the container at /app
COPY . /app

# Install any needed packages specified in requirements.txt
RUN pip install --trusted-host pypi.python.org -r requirements.txt

# Make port available to the world outside this container
EXPOSE 8000

# Run app.py when the container launches
CMD ["gunicorn", "-w", "3", "-b","0.0.0.0:8000", "app:server"]


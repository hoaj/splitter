# Use an official Python runtime as a parent image
FROM python:3.12.3-slim

# Set the working directory in the container
WORKDIR /usr/src/app

# Copy the requirements file into the container
COPY requirements.txt ./

# Install any needed packages specified in requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy the current directory contents into the container at /usr/src/app
COPY . .

# Run the main.py script when the container launches
# CMD ["python", "-m", "app.main_test"]
CMD ["uvicorn", "app.main_api:app", "--host", "0.0.0.0", "--port", "8000"]

# docker run --rm -p 8000:8000 splitter
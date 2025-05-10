FROM python:3.9-slim

# Set the working directory inside the container
WORKDIR /app

# Install system dependencies, including Tkinter
RUN apt-get update && apt-get install -y \
    gcc \
    python3-dev \
    tk \
    libtk8.6 \
    libtcl8.6 \
    && rm -rf /var/lib/apt/lists/*

# Copy only the requirements file first to leverage Docker's caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application code
COPY . .

# Set the default command to run the application
CMD ["python", "app.py"]
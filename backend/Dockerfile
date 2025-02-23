# Use a base image
FROM python:3.9

# Set the working directory inside the container
WORKDIR /app

# Copy only the requirements file first to leverage caching
COPY requirements.txt ./

# Install dependencies **before copying scripts**, so they are cached
RUN pip install --no-cache-dir -r requirements.txt


# Copy application code
COPY . .

# Copy entrypoint script inside the container
COPY backend-entrypoint.sh /backend-entrypoint.sh

# Make the script executable
RUN chmod +x /backend-entrypoint.sh

# Install json parser
RUN apt-get update && apt-get install -y jq

ENV PYTHONUNBUFFERED=1

# Set the entrypoint
ENTRYPOINT ["/bin/sh", "/backend-entrypoint.sh"]

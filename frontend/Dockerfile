# Use official Node image
FROM node:20-alpine

RUN apk add --no-cache curl jq

# Set working directory
WORKDIR /app

# Copy package.json and install dependencies first for caching
COPY package.json package-lock.json ./
RUN npm install

# Copy the entire frontend directory
COPY . .

# Copy and set entrypoint script
COPY frontend-entrypoint.sh /frontend-entrypoint.sh
RUN chmod +x /frontend-entrypoint.sh

# Expose frontend port
EXPOSE 3000

# Run the entrypoint script
ENTRYPOINT ["/bin/sh", "/frontend-entrypoint.sh"]

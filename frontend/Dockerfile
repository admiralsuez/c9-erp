# Build stage
FROM node:20-alpine as builder

WORKDIR /app

# Accept build-time API URL (defaults to localhost for local dev)
ARG VITE_API_URL=http://64.227.191.1:8000
ENV VITE_API_URL=$VITE_API_URL

# Copy package files
COPY package*.json ./

# Install dependencies
RUN npm ci

# Copy source code
COPY . .

# Build the application with the API URL baked in
RUN npm run build

# Production stage
from node:20-alpine

WORKDIR /app

# Install a simple HTTP server to serve static files
RUN npm install -g http-server

# Copy built assets from builder stage
COPY --from=builder /app/dist ./dist

# Expose port
EXPOSE 5173

# Serve the application
CMD ["http-server", "dist", "-p", "5173", "--cors"]

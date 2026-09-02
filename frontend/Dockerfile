# Build stage
FROM node:20-alpine AS builder

WORKDIR /app

# Accept build-time API URL. Default is the relative /api path (same-origin,
# reverse-proxied) which works on any domain without rebuilding.
ARG VITE_API_URL=/api
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
FROM node:20-alpine

WORKDIR /app

# 'serve -s' provides SPA fallback (deep links like /settings serve index.html)
RUN npm install -g serve

# Copy built assets from builder stage
COPY --from=builder /app/dist ./dist

# Create non-root user, give it ownership of dist
RUN addgroup -g 1001 appuser && adduser -u 1001 -G appuser -D appuser \
    && chown -R appuser:appuser /app
USER appuser

# Expose port (must match docker-compose and nginx upstream)
EXPOSE 5173

# Serve the application in SPA mode
CMD ["serve", "-s", "dist", "-l", "5173"]

# Development stage
FROM node:20-alpine

WORKDIR /app

# Copy package files and essential config files
COPY package.json pnpm-lock.yaml ./
COPY vite.config.ts tsconfig.json tsconfig.app.json tsconfig.node.json ./
COPY index.html ./

# Enable corepack and install dependencies
RUN corepack enable && pnpm install --frozen-lockfile --prod=false

# Expose port for development server
EXPOSE 5173

# Start development server with host binding for external access
CMD ["pnpm", "dev", "--host"]

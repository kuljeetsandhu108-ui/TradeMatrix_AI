# Use Node.js
FROM node:18-alpine

WORKDIR /app

# Copy package files and install
COPY package.json package-lock.json ./
RUN npm install

# Copy the rest of the frontend
COPY . .

# Build the Next.js app
RUN npm run build

# Expose port
EXPOSE 3000

# Start the app
CMD ["npm", "start"]
FROM node:23-alpine

# Create app directory
WORKDIR /usr/src/app

# Copy package.json and install dependencies
COPY package.json ./
RUN npm install

# Copy application code
COPY index.js ./

# Expose the port
EXPOSE 3030

# Command to run the application
CMD ["node", "index.js"]

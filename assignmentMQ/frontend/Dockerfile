FROM nginx:alpine

# Remove default nginx static resources
RUN rm -rf /usr/share/nginx/html/*

# Copy static resources
COPY public/ /usr/share/nginx/html/

# Copy custom nginx configuration
COPY nginx.conf /etc/nginx/conf.d/default.conf

# Expose port 80
EXPOSE 80

# Start Nginx server
CMD ["nginx", "-g", "daemon off;"]

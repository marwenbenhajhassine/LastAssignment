FROM mysql:9.3

ENV MYSQL_DATABASE=tododb
ENV MYSQL_USER=todo_user

COPY init.sql /docker-entrypoint-initdb.d/

EXPOSE 3306

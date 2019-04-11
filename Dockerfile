FROM python:3.7-alpine

# build args
ARG app_name=api-quickstart
ARG env_name=development

# run args (env vars)
ENV SESSION_SECRET="session-secret-default"
ENV JWT_SECRET="jwt-secret-default"
ENV FLASK_APP=$app_name
ENV FLASK_ENV=$env_name
ENV APP_HOST="0.0.0.0"
ENV APP_PORT=5000
ENV DB_CONN="sqlite:///app.db"

COPY requirements.txt /

RUN pip install -r /requirements.txt
COPY app/ /app
WORKDIR /app

# run container as flask webserver only
ENTRYPOINT ["/bin/sh", "entrypoint.sh"]

#!/bin/sh

export FLASK_APP
export FLASK_ENV
python run.py --host $APP_HOST --port $APP_PORT --conn $DB_CONN --sessionsecret $SESSION_SECRET --jwtsecret $JWT_SECRET

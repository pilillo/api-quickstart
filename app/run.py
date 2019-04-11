# based on:
# https://flask-restful.readthedocs.io/en/latest/quickstart.html#full-example
# https://github.com/oleg-agapov/flask-jwt-auth/blob/master/step_5/run.py

import argparse
from flask import Flask
from flask_restful import Api
from flask_sqlalchemy import SQLAlchemy
from flask_jwt_extended import JWTManager

from AppContext import AppContext

def parse_input():
    app_parser = argparse.ArgumentParser()
    app_parser.add_argument("--host", help="overwrites the default host", type=str, default="0.0.0.0")
    app_parser.add_argument("--port", help="overwrites the default server port", type=int, default=5000)
    app_parser.add_argument("--debug", help="run in debug mode", action="store_true")
    app_parser.add_argument("--conn", help="connection string", type=str, default="sqlite:///app.db")
    app_parser.add_argument("--sessionsecret", help="key to keep client-side sessions secure", type=str, required=True)
    app_parser.add_argument("--jwtsecret", help="jwt secret used for encryption", type=str, required=True)
    return app_parser.parse_args()


def app_setup(db_conn, session_secret, jwt_secret):
    ac = AppContext()
    ac.app = Flask(__name__)
    ac.api = Api(ac.app)

    # config DB connection
    ac.app.config['SQLALCHEMY_DATABASE_URI'] = db_conn
    # set track modification to false, as it is deprecated and false by default anyways
    ac.app.config['SQLALCHEMY_TRACK_MODIFICATIONS']=False
    # the secret key is used for sessions (i.e. to sign cookies)
    # this could be stored as a k8s secret and passed at creation time
    # upon renewal the services could be rolled-updated to use the newer version
    # after receiving http 403 the client will renew his session/cookie
    ac.app.config['SECRET_KEY'] = session_secret
    # create engine to interact with the DB
    ac.db = SQLAlchemy(ac.app)
    # config JWT (JSON Web Token)
    ac.app.config['JWT_SECRET_KEY'] = jwt_secret
    ac.app.config['PROPAGATE_EXCEPTIONS'] = True
    ac.jwt = JWTManager(ac.app)
    return ac


def add_resources(ac):
    import resources
    # add resources to route requests to
    ac.api.add_resource(resources.UserRegistration, '/registration')
    ac.api.add_resource(resources.UserLogin, '/login')
    ac.api.add_resource(resources.TokenRefresh, '/token/refresh')
    ac.api.add_resource(resources.UserBalance, '/balance')
    ac.api.add_resource(resources.Transaction, '/transaction')
    return ac

if __name__== "__main__":
    args = parse_input()

    # todo: sanitize inputs

    # get application context
    # app_setup(db_conn, session_secret, jwt_secret):
    ac = app_setup(args.conn, args.sessionsecret, args.jwtsecret)

    # called only when running as server (to create DB if needed)
    # in a real setup the DB should not be created by the server
    @ac.app.before_first_request
    def create_tables():
        ac.db.create_all()

    # add service endpoints
    ac = add_resources(ac)

    # start flask app
    ac.app.run(host=args.host, port=args.port, debug=args.debug)

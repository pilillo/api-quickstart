from flask_restful import Resource, reqparse
from flask_jwt_extended import (create_access_token, create_refresh_token, jwt_required, jwt_refresh_token_required, get_jwt_identity, get_raw_jwt)
from model import UserModel

from AppContext import AppContext
jwt = AppContext().jwt

# based on example at https://github.com/oleg-agapov/flask-jwt-auth/blob/master/step_5/resources.py
# parser used to validate incoming requests to manage a user profile
parser = reqparse.RequestParser()
parser.add_argument('username', help = 'This field cannot be blank', required = True)
parser.add_argument('password', help = 'This field cannot be blank', required = True)

# parser used to validate incoming requests for transactions
transaction_parser = reqparse.RequestParser()
transaction_parser.add_argument('username', help = 'This field cannot be blank', required = True)
transaction_parser.add_argument('amount', help = 'This field cannot be blank', required = True)
transaction_parser.add_argument('target', help = 'This field cannot be blank', required = True)


class UserRegistration(Resource):
    def post(self):
        data = parser.parse_args(strict=True)
        # check if user exists already
        if UserModel.find_by_username(data['username']):
            return {'message': 'User {} already exists'. format(data['username'])}
        # create a new user
        new_user = UserModel(
            username = data['username'],
            password = UserModel.generate_hash(data['password'])
        )
	# attempt saving user to the DB
        try:
            new_user.save_to_db()
            # create temporary access token
            access_token = create_access_token(identity = data['username'])
            refresh_token = create_refresh_token(identity = data['username'])

            return {
                'message': 'User {} was created'.format( data['username']),
                'access_token': access_token,
                'refresh_token': refresh_token
            }
        except:
            return {'message': 'Something went wrong while creating the user'}, 500

class UserLogin(Resource):
    def post(self):
        data = parser.parse_args(strict=True)
        current_user = UserModel.find_by_username(data['username'])

        # make sure the user exists
        if not current_user:
            return {'message': 'User {} doesn\'t exist'.format(data['username'])}

        # check if the provided password is correct
        if UserModel.verify_hash(data['password'], current_user.password):
            access_token = create_access_token(identity = data['username'])
            refresh_token = create_refresh_token(identity = data['username'])
            return {
                'message': 'Logged in as {}'.format(current_user.username),
                'access_token': access_token,
                'refresh_token': refresh_token
            }
        else:
            return {'message': 'Wrong credentials'}


class TokenRefresh(Resource):
    @jwt_refresh_token_required
    def post(self):
        # get the user from the refresh token
        current_user = get_jwt_identity()
        # create a new access token using the user details (i.e. username)
        access_token = create_access_token(identity = current_user)
        return {'access_token': access_token}

class UserLogout(Resource):
    def post(self):
        pass

class UserBalance(Resource):
    @jwt_required
    def get(self):
        # Access the identity of the current user with get_jwt_identity
        current_user = UserModel.find_by_username(get_jwt_identity())
        return {
            'username': current_user.username,
            'balance': current_user.balance
        }


class Transaction(Resource):
    @jwt_required
    def post(self):
        # validate request
        data = transaction_parser.parse_args()
        # make sure the target user exists
        target_user = UserModel.find_by_username(data['target'])
        # make sure the user exists
        if not target_user:
            return {'message': 'Target user {} doesn\'t exist'.format(data['target'])}
        # check if the user has the credit he wants to transfer
        current_user = UserModel.find_by_username(get_jwt_identity())
        amount = float(data['amount'])
        if amount <= 0.0:
            return {'message' : 'A transaction is expected to have an amount greater than 0'}
        if current_user.balance < amount:
            return {'message': 'User {} requested to transfer {} to user {}, however the credit is not enough'.format(data['username'], data['amount'], data['target'])}
        # if we reached here the target user exists and we have enough credit, then perform the transaction
        try:
            UserModel.transact(current_user, amount, target_user)
            return {'message':'Successfully moved {} from {} to {}'.format(data['amount'], data['username'], data['target']) }
        except:
            return {'message': 'Something went wrong while moving {} to user {}'.format(data['amount'], target_user.username)}, 500

from flask import Flask
from flask_restful import Api
from flask_sqlalchemy import SQLAlchemy
from flask_jwt_extended import JWTManager
from passlib.hash import pbkdf2_sha256 as sha256
import pytest
import json

from AppContext import AppContext

from run import app_setup, add_resources

@pytest.fixture(scope="session")
def ac():
    ac = app_setup("sqlite:///:memory:", "session_secret", "jwt_secret")
    #ac = app_setup("sqlite:///test.db", "session_secret", "jwt_secret")

    @ac.app.before_first_request
    def create_tables():
        ac.db.create_all()

    ac = add_resources(ac)
    return ac

@pytest.fixture
def app(ac):
    return ac.app


def test_methods(client):
    # make sure only POST is allowed
    post_endpoints = ["/login","/registration","/token/refresh","/transaction"]
    for ep in post_endpoints:
        response = client.get(ep)
        assert response.status_code == 405
    # make sure only GET is allowed for balance
    response = client.post("/balance")
    assert response.status_code == 405

def test_protected(client):
    # make sure /balance and /transaction are not accessible when unlogged
    response = client.get("/balance")
    # expect 401 unauthorized
    assert response.status_code == 401
    # expect 401 unauthorized
    response = client.post("/transaction")
    assert response.status_code == 401


@pytest.fixture(scope="session")
def db_creation(ac):
    # populate db
    ac.db.create_all()


@pytest.fixture(scope="session")
def add_user(db_creation, ac):
    from model import UserModel
    new_user = UserModel(
        username = "test",
        password = sha256.hash("test")
    )
    new_user.save_to_db()


def test_registration(db_creation, client, ac):
    headers = {
        'Content-Type': 'application/json',
        'Accept': 'application/json'
    }
    body = {
        'username' : 'gilberto',
        'password' : 'test'
    }
    response = client.post("/registration", data=json.dumps(body), headers=headers)
    # make sure the newly created user exists
    from model import UserModel
    usr = UserModel.find_by_username("gilberto")
    assert usr is not None


def test_login(db_creation, add_user, client, ac):
    headers = {
        'Content-Type': 'application/json',
        'Accept': 'application/json'
    }
    body = {
        #'username' : 'test',
        'password' : 'test' 
    }
    response = client.post("/login", data=json.dumps(body), headers=headers)
    assert response.status_code == 400
    assert json.loads(response.data)["message"]["username"] == "This field cannot be blank"
    # testing the login of a non-existing user
    body = {
        'username' : 'test-wrong',
        'password' : 'test'
    }
    response = client.post("/login", data=json.dumps(body), headers=headers)
    assert response.status_code == 200
    assert json.loads(response.data)["message"] == "User test-wrong doesn't exist"
    # testing wrong password 
    body = {
        'username' : 'test',
        'password' : 'test-wrong'
    }
    response = client.post("/login", data=json.dumps(body), headers=headers)
    assert response.status_code == 200
    assert json.loads(response.data)["message"] == "Wrong credentials"
    # testing the correct login on an existing user
    body = {
        'username' : 'test',
        'password' : 'test'
    }
    response = client.post("/login", data=json.dumps(body), headers=headers)
    assert response.status_code == 200
    assert "Logged in as test" == json.loads(response.data)["message"]
    assert "access_token" in json.loads(response.data).keys()
    assert "refresh_token" in json.loads(response.data).keys()


def test_balance(db_creation, add_user, client, ac):
    # login user
    headers = {
        'Content-Type': 'application/json',
        'Accept': 'application/json'
    }
    body = {
        'username' : 'test',
        'password' : 'test'
    }
    response = client.post("/login", data=json.dumps(body), headers=headers)
    logged_user = json.loads(response.data)
    # add access token to JWT request
    headers["Authorization"] = "Bearer "+logged_user["access_token"]+"some garbage"
    # get balance
    response = client.get("/balance", data=json.dumps(body), headers=headers)
    assert response.status_code == 400 or response.status_code == 422
    # get balance with correct request
    headers["Authorization"] = "Bearer "+logged_user["access_token"]
    response = client.get("/balance", data=json.dumps(body), headers=headers)
    assert response.status_code == 200
    assert json.loads(response.data)["balance"] == 0.0


def test_transactions(db_creation, add_user, client, ac):
    # login user
    headers = {
        'Content-Type': 'application/json',
        'Accept': 'application/json'
    }
    body = {
        'username' : 'test',
        'password' : 'test'
    }
    response = client.post("/login", data=json.dumps(body), headers=headers)
    logged_user = json.loads(response.data)

    # change body to perform a transaction from a user to another one
    body = {
        'username' : 'test',
        'amount' : '10'
    }

    # attempt transaction with wrong jwt access token
    headers["Authorization"] = "Bearer "+logged_user["access_token"]+"some garbage"
    response = client.post("/transaction", data=json.dumps(body), headers=headers)
    assert response.status_code == 422

    # attempt transaction to non existing user
    headers["Authorization"] = "Bearer "+logged_user["access_token"]
    body['target'] = "non-existing"
    response = client.post("/transaction", data=json.dumps(body), headers=headers)
    assert response.status_code == 200
    assert json.loads(response.data)['message'] == "Target user non-existing doesn't exist"

    # attemp transaction, without credit, it should fail
    body['target'] = "gilberto"
    response = client.post("/transaction", data=json.dumps(body), headers=headers)
    assert response.status_code == 200
    assert "however the credit is not enough" in  json.loads(response.data)['message']

    # add credit and retry transaction, this should succeed
    from model import UserModel
    usr_test = UserModel.find_by_username("test")
    usr_gilberto = UserModel.find_by_username("gilberto")
    usr_test.balance = 10.0
    ac.db.session.commit()
    response = client.post("/transaction", data=json.dumps(body), headers=headers)
    assert response.status_code == 200
    assert "Successfully moved 10 from test to gilberto" == json.loads(response.data)["message"]
    usr_test = UserModel.find_by_username("test")
    assert usr_test.balance == 0
    usr_gilberto = UserModel.find_by_username("gilberto")
    assert usr_gilberto.balance == 10.0

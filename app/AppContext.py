class AppContext:
    _app = None
    _api = None
    _db = None
    _jwt = None

    def set_app(self, app):
        type(self).app = app

    def get_app(self):
        return type(self)._app

    def set_api(self, api):
        type(self)._api = api

    def get_api(self):
        return type(self)._api

    def set_db(self, db):
        type(self)._db = db

    def get_db(self):
        return type(self)._db

    def set_jwt(self, jwt):
        type(self)._jwt = jwt

    def get_jwt(self):
        return type(self)._jwt

    app = property(get_app, set_app)
    api = property(get_api, set_api)
    db = property(get_db, set_db)
    jwt = property(get_jwt, set_jwt)

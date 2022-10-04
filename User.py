from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash


class User():
    # при запросе от браузера (user_loader)
    def fromdB(self, user_id, db):
        self.__user = db.get_user(user_id)
        return self
    # при авторизации на сайте
    def create(self, user):
        self.__user = user
        return self

    def is_authenticated(self):
        return True

    def is_active(self):
        return True

    def is_anonymous(self):
        return False

    def get_id(self):
        return str(self.__user[0])

    def get_name(self):
        try:
            n = str(self.__user[1])
            print("////////", n)
            return n
        except:
            return ""

    def get_role(self):
        return str(self.__user[2])

    def get_phone(self):
        return str(self.__user[3])

    def get_email(self):
        return str(self.__user[4])

    def get_password(self):
        return str(self.__user[5])


    # password_hash = '12345'
    # @property
    # def password(self):
    #     raise AttributeError('password is not a readable attribute')
    #
    # @password.setter
    # def password(self, password):
    #     self.password_hash = generate_password_hash(password)
    #
    # def verify_password(self, password):
    #     return check_password_hash(self.password_hash, password)

from flask_login import current_user


class UsersPolicy:
    def __init__(self, record=None):
        self.record = record

    def create(self):
        return current_user.role_id == 1

    def delete(self):
        return current_user.role_id == 1

    def show(self):
        return True

    def update(self):
        return current_user.role_id == 2

    def show_collections(self):
        return current_user.role_id != 2 and current_user.role_id != 1
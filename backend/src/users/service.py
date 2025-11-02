

class UserService:
    def __init__(self, user_repository: UserRepository):
        self.user_repository = user_repository

    def create_user_URL(self, user: UserCreate) -> str:
        return self.user_repository.create_user_URL(user)
class ServiceError(Exception):
    pass


class AuthenticationError(ServiceError):
    def __init__(self, message: str = "Invalid email or password."):
        super().__init__(message)


class AuthorizationError(ServiceError):
    pass


class AlreadyExistsError(ServiceError):
    pass


class NotFoundError(ServiceError):
    pass



class CustomException(Exception):
    DEFAULT_ERROR_MESSAGE = "Exception occurred"

    def __init__(self, error_message: str = None):
        error_message = error_message or self.DEFAULT_ERROR_MESSAGE
        self.error_message = error_message
        super().__init__(self.error_message)
        print(f"Exception occurred: {self.error_message}")


class ApiException(CustomException):
    DEFAULT_ERROR_MESSAGE = "API Exception"
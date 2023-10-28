class PermissionDeniedError(Exception):
    def __init__(self, message="Permission denied. User does not have the required permissions."):
        super().__init__(message)
        
        
class NotExistedChat(Exception):
    def __init__(self, message='Chat does not exist.'):
        super().__init__(message)
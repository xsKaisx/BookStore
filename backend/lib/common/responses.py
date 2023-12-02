from rest_framework import status
from rest_framework.response import Response
from datetime import datetime

class GenerateResponse:
    headers = {'Content-Type': 'application/json'}
    
    @classmethod
    def create_response(cls, message: str, data, status: status):
        res = Response(
            data = {'message': message, 'data': data, 'created_at': str(datetime.utcnow())},
            status = status,
            headers = cls.headers
        )
        return res
    
    @classmethod
    def success(cls, message: str = 'success', data = None, status = status.HTTP_200_OK):
        return cls.create_response(message=message, data=data, status=status)
    
    @classmethod
    def created(cls, message: str = 'created', data = None, status = status.HTTP_201_CREATED):
        return cls.create_response(message=message, data=data, status=status)
    
    @classmethod
    def failed(cls, message: str = 'failed', data = None, status = status.HTTP_400_BAD_REQUEST):
        return cls.create_response(message=message, data=data, status=status)
    
    @classmethod
    def unauthorized(cls, message: str = 'you are not allowed to make this request', data = None, status = status.HTTP_401_UNAUTHORIZED):
        return cls.create_response(message=message, data=data, status=status)
    
    @classmethod
    def something_went_wrong(cls):
        return cls.failed(message = 'something went wrong', data=None)
    
helper_response = GenerateResponse()
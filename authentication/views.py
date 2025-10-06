from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework_simplejwt.tokens import RefreshToken

from authentication.serializers import LoginSerializer, UserRegistrationSerializer
from expenses_backend import generics
from expenses_backend.response_messages import ResponseMessages
from expenses_backend.response_schemas import create_api_response, convert_serializer_errors

response_messages = ResponseMessages()

class LoginAPIView(generics.GenericAPIView):
    """
    API view to authenticate a user and return JWT tokens along with user details.
    """
    permission_classes = [AllowAny]
    serializer_class = LoginSerializer

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)

        if not serializer.is_valid():
            return create_api_response(
                request,
                status_code=status.HTTP_400_BAD_REQUEST,
                message=response_messages.bad_response,
                data=convert_serializer_errors(serializer.errors)
            )

        user = serializer.validated_data.get("user")
        if not user:
            return create_api_response(
                request,
                status_code=status.HTTP_401_UNAUTHORIZED,
                message="Invalid credentials",
                data={}
            )
        
        try:
            refresh = RefreshToken.for_user(user)

            return create_api_response(
                request,
                status_code=status.HTTP_200_OK,
                message="Login successful",
                data={
                    "token": str(refresh.access_token),
                    "refresh": str(refresh),
                    "user_id": user.id,
                    "email": user.email,
                    "username": user.username,
                    "company_name": getattr(user, "company_name", None)
                }
            )

        except Exception as e:
            return create_api_response(
                request,
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                message="An unexpected error occurred",
                data={"error": str(e)}
            )


class RegisterAPIView(generics.GenericAPIView):
    """
    API view to register a new user and return JWT tokens.
    """
    permission_classes = [AllowAny]
    serializer_class = UserRegistrationSerializer

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)

        if not serializer.is_valid():
            return create_api_response(
                request,
                status_code=status.HTTP_400_BAD_REQUEST,
                message="Validation failed",
                data=convert_serializer_errors(serializer.errors)
            )

        try:
            user = serializer.save()
            refresh = RefreshToken.for_user(user)

            return create_api_response(
                request,
                status_code=status.HTTP_201_CREATED,
                message="Registration successful",
                data={
                    "token": str(refresh.access_token),
                    "refresh": str(refresh),
                    "user_id": user.id,
                    "email": user.email,
                    "username": user.username,
                    "company_name": getattr(user, "company_name", None)
                }
            )

        except Exception as e:
            return create_api_response(
                request,
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                message="Registration failed",
                data={"error": str(e)}
            )
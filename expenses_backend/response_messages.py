from dataclasses import dataclass

@dataclass
class _StandardResponses():
    """
    A container class for standard response messages used throughout the application.

    Methods:
        create_custom_message
    Attributes:
        bad_response (str): Message returned when data validation fails.
        internal_server_error_response (str): Message returned when a server error occurs.
    """

    bad_response: str = 'Something went wrong while validating data, please check your data.'
    internal_server_error_response: str = 'server error occured please try again.'

    def create_custom_message(self, message: str) -> str:
        """
        Creates and returns a custom message.

        Args:
            message (str): The message to be returned.

        Returns:
            str: The same message that was provided as input.
        """
        return message


class ChatBotMessages(_StandardResponses):
    
    chat_message_success = 'Question answered successfully!'


class ResponseMessages(_StandardResponses):
    """
    ResponseMessages provides standardized response messages for the application.

    Attributes:
        chatbot (ChatBotMessages): Contains chatbot-related response messages.
    """

    chatbot: ChatBotMessages = ChatBotMessages()

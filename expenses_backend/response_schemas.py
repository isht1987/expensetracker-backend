from typing import Union, List, Dict, Any, Type

from django.http import JsonResponse

from rest_framework import serializers, status
from rest_framework.utils.serializer_helpers import ReturnDict, ReturnList
from rest_framework.request import Request

from drf_yasg import openapi


def convert_serializer_errors(errors: dict) -> Union[Dict[str, Any], List[Dict[str, Any]]]:
    """
    Converts a Django serializer error object into a standardized API response.

    Parameters:
    errors (dict): A Django serializer error object.

    Returns:
    dict: A standardized API response.
    """
    data = {}  # Initialize an empty dictionary to hold the standardized API response.

    # If the errors object is a list, it represents a list of dictionaries with errors for multiple objects.
    if isinstance(errors, list):
        # Initialize an empty list to hold individual response data.
        response = []

        for error_dict in errors:
            for field, field_errors in error_dict.items():
                error_list = []
                for field_error in field_errors:
                    # Convert the error message for 'null' field to a more human-readable format.
                    error_list.append("This field is required." if str(
                        field_error) == 'This field may not be null.' else str(field_error))
                # Combine error messages into a comma-separated string.
                data[field] = ', '.join(error_list)
            # Append individual response data to the main response list.
            response.append(data)

        # Return the list of individual response data for multiple objects.
        return response

    # If the errors object is a dictionary, it represents errors for a single object.
    for field, field_errors in errors.items():
        error_list = []

        # If the field_errors is a dictionary, it represents nested field errors.
        if isinstance(field_errors, dict):
            sub_data = {}
            for sub_field, sub_field_errors in field_errors.items():
                sub_error_list = []
                for sub_field_error in sub_field_errors:
                    # Convert the error message for 'null' field to a more human-readable format.
                    sub_error_list.append("This field is required." if str(
                        sub_field_error) == 'This field may not be null.' else str(sub_field_error))
                # Combine nested error messages.
                sub_data[sub_field] = ', '.join(sub_error_list)
            # Assign the nested error data to the corresponding field.
            data[field] = sub_data

        # If the field_errors is a list, it represents errors for a single field.
        else:
            for field_error in field_errors:
                # Convert the error message for 'null' field to a more human-readable format.
                error_list.append("This field is required." if str(
                    field_error) == 'This field may not be null.' else str(field_error))
            # Combine error messages into a comma-separated string.
            data[field] = ', '.join(error_list)

    return data  # Return the standardized API response dictionary.


def get_status_from_code(status_code: int) -> str:
    """
    Returns the status of an HTTP response based on its status code.

    Parameters:
    status_code (int): The HTTP status code.

    Returns:
    str: The status of the response.
    """

    if status_code >= 100 and status_code < 200:
        return 'info'
    elif status_code >= 200 and status_code < 300:
        return 'success'
    elif status_code >= 300 and status_code < 400:
        return 'warning'
    else:
        return 'error'


def has_id_at_end(url: str) -> bool:
    """
    Checks if there is an ID at the end of the URL path.

    Args:
        url (str): The URL to check.

    Returns:
        bool: True if the URL has an ID at the end, False otherwise.
    """

    # Remove trailing slashes if present
    url = url.rstrip('/')

    # Split the path into segments
    segments = url.split('/')

    # Check if the last segment is a numeric ID
    last_segment = segments[-1]
    return last_segment.isdigit()


def create_api_response(request: Request, status_code: int, message: str, data: Union[List[Dict[str, Any]], Dict[str, Any], None] = None) -> JsonResponse:
    """
    Creates a standardized API response.

    Parameters:
    status_code (int): The HTTP status code of the response.
    message (str): A human-readable message providing more information about the response.
    data (dict or None): Additional data that may be relevant to the response.

    Returns:
    JsonResponse: A standardized JSON API response.
    """
    try:
        response = {
            'status': get_status_from_code(status_code),
            'message': message,
            'data': {}
        }
        if data is not None:
            response['data'] = data
        else:

            if request.method == 'GET':
                if has_id_at_end(request.path):
                    response['data'] = {}
                else:
                    response['data'] = []
            else:
                response['data'] = {}

        return JsonResponse(response, status=status_code)
    except Exception as e:
        error_message = f"Error creating API response: {e}"
        error_data = {'error': str(e)}
        return JsonResponse({
            'status': 'error',
            'message': error_message,
            'data': error_data
        }, status=500)


def get_responses_dict(
        method: str = 'GET',
        serializer_class: Union[
            Type[serializers.ModelSerializer],
            Type[serializers.Serializer],
            Type[serializers.ListSerializer],
            Type[serializers.HyperlinkedModelSerializer],
            None
        ] = None,
        success_message: str = "success_message",
        error_message: str = "error_message",
        not_found_message: str = "Instance with ID not found.",
        paginated_response: bool = False,
        many: bool = False,
        hide_password: bool = False,
        additional_data: Union[Dict[str, Any], None] = None,
        remove_fields: List[str] = []
) -> Dict[str, Any]:
    """
    Generates a dictionary of OpenAPI response schemas for a given HTTP method, serializer, and response configuration.
    Args:
        method (str): The HTTP method for which to generate responses ('GET', 'POST', 'PUT', 'DELETE'). Defaults to 'GET'.
        serializer_class (Union[Type[serializers.ModelSerializer], Type[serializers.Serializer], Type[serializers.ListSerializer], Type[serializers.HyperlinkedModelSerializer], None]):
            The DRF serializer class to use for generating example data and schema. Optional.
        success_message (str): The message to include in successful responses. Defaults to "success_message".
        error_message (str): The message to include in error responses. Defaults to "error_message".
        not_found_message (str): The message to include in 404 responses. Defaults to "Instance with ID not found.".
        paginated_response (bool): Whether to use a paginated response schema for GET requests. Defaults to False.
        many (bool): Whether the response data should be a list (for multiple objects). Defaults to False.
        hide_password (bool): Whether to remove 'password' fields from the response data. Defaults to False.
        additional_data (Union[Dict[str, Any], None]): Additional data to include in the response. Optional.
        remove_fields (List[str]): List of field names to remove from the response data. Defaults to [].
    Returns:
        Dict[str, Any]: A dictionary mapping HTTP status codes to OpenAPI response objects, configured according to the provided arguments.
    """

    responses = {}
    data = {}
    serializer = None

    if serializer_class:

        serializer = serializer_class(data={'':""})

        data = serializer_class().data
        if isinstance(data, ReturnDict):
            keys = list(data.keys())
            if any([key for key in keys if key.find('password')]) and hide_password:
                data.pop('password')

            if remove_fields:
                if any([key for key in keys if key in remove_fields]):
                    for fields in remove_fields:
                        data.pop(fields)

        serializer.is_valid()

    responsesGET200 = openapi.Response(
        description="Success",
        examples={
            'application/json': {
                'status': 'success',
                    'message': success_message,
                    'data': {
                        'count': 0,
                        'next': 'https://www.example.com/?page=3',
                        'previous': 'https://www.example.com/?page=1',
                        'result': [data if serializer_class else None] if many else data if serializer_class else {}
                    }
            }
        },
        schema=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'status': openapi.Schema(type=openapi.TYPE_STRING, default='success'),
                'message': openapi.Schema(type=openapi.TYPE_STRING, default=success_message),
                'data': openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'count': openapi.Schema(type=openapi.TYPE_INTEGER, default=0),
                        'next': openapi.Schema(type=openapi.TYPE_STRING, default=''),
                        'previous': openapi.Schema(type=openapi.TYPE_STRING, default=''),
                        'results': openapi.Schema(
                            type=openapi.TYPE_ARRAY if many else openapi.TYPE_OBJECT,
                            items=openapi.Schema(
                                type=openapi.TYPE_OBJECT,
                            ) if many else None
                        )
                    },
                    required=['results']
                )
            },
            required=['status', 'message', 'data']
        )
    ) if paginated_response else openapi.Response(
        description="Success",
        examples={
            'application/json': {
                'status': 'success',
                'message': success_message,
                'data': [data if serializer_class else None] if many else data if serializer_class else {}
            }
        },
        schema=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'status': openapi.Schema(type=openapi.TYPE_STRING, default='success'),
                'message': openapi.Schema(type=openapi.TYPE_STRING, default=success_message),
                'data': openapi.Schema(
                    type=openapi.TYPE_ARRAY if many else openapi.TYPE_OBJECT,
                    items=openapi.Schema(
                        type=openapi.TYPE_OBJECT,
                    ) if many else None
                )
            },
            required=[
                'status', 'message', 'data']
        )
    )

    responsesPOST200 = openapi.Response(
        description="Success",
        examples={
            'application/json': {
                'status': 'success',
                    'message': success_message,
                    'data':  additional_data if additional_data else data if serializer_class else {}
            }
        },
        schema=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'status': openapi.Schema(type=openapi.TYPE_STRING, default='success'),
                'message': openapi.Schema(type=openapi.TYPE_STRING, default=success_message),
                'data': openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                )
            },
            required=['status', 'message', 'data']
        )
    )

    responsesDELETE200 = openapi.Response(
        description="Success",
        examples={
            'application/json': {
                'status': 'success',
                    'message': success_message,
                    'data': {}
            }
        },
        schema=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'status': openapi.Schema(type=openapi.TYPE_STRING, default='success'),
                'message': openapi.Schema(type=openapi.TYPE_STRING, default=success_message),
                'data': openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                )
            },
            required=['status', 'message', 'data']
        )
    )

    responses400 = openapi.Response(
        description="Error",
        examples={
            'application/json': {
                'status': 'Error',
                    'message': error_message,
                    'data': serializer.errors if serializer else {}
            }
        },
        schema=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'status': openapi.Schema(type=openapi.TYPE_STRING, default='Error'),
                'message': openapi.Schema(type=openapi.TYPE_STRING, default=error_message),
                'data': openapi.Schema(
                    type=openapi.TYPE_ARRAY,
                    items=openapi.Schema(
                        type=openapi.TYPE_OBJECT,
                    )
                )
            },
            required=['status', 'message', 'data']
        )
    )

    responses404 = openapi.Response(
        description="Error",
        examples={
            'application/json': {
                'status': 'Error',
                    'message': error_message if not not_found_message else not_found_message,
                    'data': {'error': 'Oops! There is no Data with ID'}
            }
        },
        schema=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'status': openapi.Schema(type=openapi.TYPE_STRING, default='Error'),
                'message': openapi.Schema(type=openapi.TYPE_STRING, default=error_message),
                'data': openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'error': openapi.Schema(type=openapi.TYPE_STRING, default=''),
                    },
                    required=['results']
                )
            },
            required=['status', 'message', 'data']
        )
    )

    if method.lower() == 'get':
        responses = {"200": responsesGET200, "404": responses404}

    if method.lower() == 'post':
        responses = {"200": responsesPOST200, "400": responses400}

    if method.lower() == 'put':
        responses = {"200": responsesPOST200, "400": responses400, "404": responses404}

    if method.lower() == 'delete':
        responses = {"200": responsesDELETE200,
                     "404": responses404}

    return responses


def get_query_parameters(method: str = 'GET', filters: bool = False, search: bool = False, pagination: bool = False) -> List[openapi.Parameter]:
    """
    Generates a list of OpenAPI query parameters based on the provided options.
    Args:
        method (str, optional): The HTTP method for which to generate parameters. Defaults to 'GET'.
        filters (bool, optional): If True, includes a 'filter' query parameter. Defaults to False.
        search (bool, optional): If True, includes a 'search' query parameter. Defaults to False.
        pagination (bool, optional): If True, includes 'page' and 'page_size' query parameters. Defaults to False.
    Returns:
        list: A list of OpenAPI Parameter objects corresponding to the requested query parameters.
    """

    parameters = []

    if filters:
        parameters.append(openapi.Parameter(
            name='filter',
            in_=openapi.IN_QUERY,
            description='Filter parameter',
            type=openapi.TYPE_STRING
        ))

    if search:
        parameters.append(openapi.Parameter(
            name='search',
            in_=openapi.IN_QUERY,
            description='Search parameter',
            type=openapi.TYPE_STRING
        ))

    if pagination:
        parameters.append(openapi.Parameter(
            name='page',
            in_=openapi.IN_QUERY,
            description='Page number',
            type=openapi.TYPE_INTEGER
        ))
        parameters.append(openapi.Parameter(
            name='page_size',
            in_=openapi.IN_QUERY,
            description='Page size',
            type=openapi.TYPE_INTEGER
        ))

    return parameters

"""Centralized API request routing and logging."""

import time
from typing import Callable

import orjson
from fastapi import Request, Response
from fastapi.exceptions import HTTPException, RequestValidationError, ResponseValidationError
from fastapi.responses import ORJSONResponse
from fastapi.routing import APIRoute
from pydantic import ValidationError
from starlette.status import HTTP_400_BAD_REQUEST, HTTP_500_INTERNAL_SERVER_ERROR

from ai_agents.leadgen.schemas.ai_agents import ResponseData


class CustomRequestRoute(APIRoute):
    def get_route_handler(self) -> Callable:
        original_route_handler = super().get_route_handler()

        async def custom_route_handler(request: Request) -> Response:
            request_data = await process_request_data(request=request)
            start_time = time.perf_counter()

            try:
                content_type = request.headers.get("content-type")
                request_data['request_body'] = orjson.loads(request_data['request_body']) \
                    if request_data['request_body'] and not content_type.startswith("multipart/form-data") else {}
                response: Response = await original_route_handler(request)
                end_time = time.perf_counter()
                request_data['request_duration'] = end_time - start_time
                response_data = {
                    'status_code': response.status_code,
                    'body': orjson.loads(response.body.decode('utf-8'))
                }
                print(f"HTTP request for {request_data['url_path']} with method {request.method}")
                print(f"Request data: {request_data}")
                print(f"Response data: {response_data}")

                # Ensure the response content is cleaned from any leading or trailing newline characters
                response.content = response.body.strip()
                return response

            except orjson.JSONDecodeError as exc:
                return request_exception_handler(method=request.method, url_path=request_data['url_path'],
                                                 request_data=request_data, exc=exc,
                                                 start_time=start_time, status_code=HTTP_400_BAD_REQUEST)

            except (RequestValidationError, ValidationError, ResponseValidationError) as exc:
                errors = get_formatted_pydantic_errors(validation_error=exc)
                return request_exception_handler(method=request.method, url_path=request_data['url_path'],
                                                 request_data=request_data, exc=errors,
                                                 start_time=start_time, status_code=HTTP_400_BAD_REQUEST,
                                                 is_validation_error=True)

            except HTTPException as exc:
                return request_exception_handler(method=request.method, url_path=request_data['url_path'],
                                                 request_data=request_data, exc=exc.detail,
                                                 start_time=start_time, status_code=exc.status_code)

            except Exception as exc:
                return request_exception_handler(method=request.method, url_path=request_data['url_path'],
                                                 request_data=request_data, exc=exc,
                                                 start_time=start_time, status_code=HTTP_500_INTERNAL_SERVER_ERROR)

        return custom_route_handler


async def process_request_data(request: Request) -> dict:
    # Parse x-user-data header if present
    headers = dict(request.headers)

    if x_user_data_str := headers.get("x-user-data"):
        try:
            x_user_data = orjson.loads(x_user_data_str)
            # Store parsed version for logging
            headers['x-user-data'] = x_user_data

        except Exception as e:
            print("Failed to parse x-user-data header",
                  header=x_user_data_str,
                  error_type=type(e).__name__,
                  error_message=str(e))

    request_data = {
        'client_host': f"{request.client.host}:{request.client.port}" if request.client else None,
        'url': str(request.url),
        'url_path': request.scope['route'].path,
        'request_method': request.method,
        'path_params': dict(request.path_params),
        'query_params': dict(request.query_params),
        'headers': headers,
        'request_body': await request.body()
    }

    return request_data


def request_exception_handler(method=None, url_path=None, request_data=None, exc=None, start_time=None,
                              status_code=None, is_validation_error=False) -> Response:
    request_data["error"] = exc if isinstance(exc, list) else [str(exc)]
    end_time = time.perf_counter()
    request_data['request_duration'] = end_time - start_time

    # Use warning for validation errors, exception for others
    if is_validation_error:
        print(
            f"Validation Error Occurred {str(exc)}", request_data=request_data)
    else:
        print(f"Exception Occurred {str(exc)}", request_data=request_data)

    error_response = ResponseData.model_construct(
        errors=request_data["error"], success=False).dict()

    return ORJSONResponse(content=error_response, status_code=status_code)


def get_formatted_pydantic_errors(validation_error: ValidationError):
    formatted_validation_errors = [
        {"msg": f"{error['loc'][-1]}: {error['msg']}", "location": error["loc"]} for error in validation_error.errors()
    ]

    return formatted_validation_errors

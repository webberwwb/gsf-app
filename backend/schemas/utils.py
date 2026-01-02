"""Utility functions for schema validation"""
from flask import jsonify
from marshmallow import ValidationError


def validate_request(schema_class, data=None, **kwargs):
    """
    Validate request data using a Marshmallow schema.
    
    Args:
        schema_class: The schema class to use for validation
        data: The data to validate (if None, will get from request.get_json())
        **kwargs: Additional arguments to pass to schema
    
    Returns:
        tuple: (validated_data, error_response, status_code)
        If validation succeeds: (validated_data, None, None)
        If validation fails: (None, error_response, 400)
    """
    from flask import request, current_app
    
    if data is None:
        # Log request details before parsing
        current_app.logger.info(f'validate_request - Content-Type: {request.content_type}, Method: {request.method}')
        current_app.logger.info(f'validate_request - Headers: Content-Type={request.headers.get("Content-Type")}, Content-Length={request.headers.get("Content-Length")}')
        
        # Try to get JSON data
        data = request.get_json(force=False, silent=True)
        
        # If get_json returns None, try to get raw data
        if data is None:
            raw_data = request.get_data(as_text=True)
            current_app.logger.warning(f'validate_request - request.get_json() returned None. Raw data: {raw_data[:200] if raw_data else "empty"}')
            
            # Try to parse as JSON manually if Content-Type suggests JSON
            if request.content_type and 'application/json' in request.content_type.lower():
                import json
                try:
                    if raw_data:
                        data = json.loads(raw_data)
                        current_app.logger.info(f'validate_request - Successfully parsed JSON manually')
                    else:
                        current_app.logger.error(f'validate_request - No raw data available')
                except json.JSONDecodeError as e:
                    current_app.logger.error(f'validate_request - JSON decode error: {e}')
    
    if data is None:
        current_app.logger.error(f'validate_request - No data provided. Content-Type: {request.content_type}, Method: {request.method}')
        return None, jsonify({'error': 'No data provided', 'content_type': request.content_type, 'method': request.method}), 400
    
    try:
        schema = schema_class(**kwargs)
        validated_data = schema.load(data)
        return validated_data, None, None
    except ValidationError as err:
        # Format validation errors nicely
        error_messages = []
        for field, messages in err.messages.items():
            if isinstance(messages, list):
                for message in messages:
                    error_messages.append(f"{field}: {message}")
            else:
                error_messages.append(f"{field}: {messages}")
        
        return None, jsonify({
            'error': 'Validation failed',
            'messages': error_messages,
            'details': err.messages
        }), 400
    except Exception as e:
        return None, jsonify({
            'error': 'Validation error',
            'message': str(e)
        }), 400




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
    from flask import request
    
    if data is None:
        data = request.get_json()
    
    if data is None:
        return None, jsonify({'error': 'No data provided'}), 400
    
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


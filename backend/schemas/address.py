"""Address request/response schemas"""
from marshmallow import Schema, fields, validate, EXCLUDE


class CreateAddressSchema(Schema):
    """Schema for creating an address"""
    recipient_name = fields.String(required=True, validate=validate.Length(min=1, max=255))
    phone = fields.String(required=True, validate=validate.Length(min=1, max=20))
    address_line1 = fields.String(required=True, validate=validate.Length(min=1, max=255))
    address_line2 = fields.String(allow_none=True, validate=validate.Length(max=255))
    city = fields.String(required=True, validate=validate.Length(min=1, max=100))
    province = fields.String(required=True, validate=validate.Length(min=1, max=100))
    postal_code = fields.String(required=True, validate=validate.Length(min=1, max=20))
    country = fields.String(missing='Canada', validate=validate.Length(max=100))
    delivery_instructions = fields.String(allow_none=True)
    is_default = fields.Boolean(missing=False)
    
    class Meta:
        unknown = EXCLUDE


class UpdateAddressSchema(Schema):
    """Schema for updating an address"""
    recipient_name = fields.String(allow_none=True, validate=validate.Length(min=1, max=255))
    phone = fields.String(allow_none=True, validate=validate.Length(min=1, max=20))
    address_line1 = fields.String(allow_none=True, validate=validate.Length(min=1, max=255))
    address_line2 = fields.String(allow_none=True, validate=validate.Length(max=255))
    city = fields.String(allow_none=True, validate=validate.Length(min=1, max=100))
    province = fields.String(allow_none=True, validate=validate.Length(min=1, max=100))
    postal_code = fields.String(allow_none=True, validate=validate.Length(min=1, max=20))
    country = fields.String(allow_none=True, validate=validate.Length(max=100))
    delivery_instructions = fields.String(allow_none=True)
    is_default = fields.Boolean(allow_none=True)
    
    class Meta:
        unknown = EXCLUDE


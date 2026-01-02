"""Address request/response schemas"""
from marshmallow import Schema, fields, EXCLUDE


class CreateAddressSchema(Schema):
    """Schema for creating an address"""
    recipient_name = fields.String(required=True)
    phone = fields.String(required=True)
    address_line1 = fields.String(required=True)
    address_line2 = fields.String(allow_none=True, missing=None)
    city = fields.String(required=True)
    postal_code = fields.String(required=True)
    country = fields.String(missing='Canada')  # Not required, backend sets to 'Canada'
    delivery_instructions = fields.String(allow_none=True, missing=None)
    notification_email = fields.String(allow_none=True, missing=None)
    is_default = fields.Boolean(missing=False)
    
    class Meta:
        unknown = EXCLUDE


class UpdateAddressSchema(Schema):
    """Schema for updating an address"""
    recipient_name = fields.String(allow_none=True)
    phone = fields.String(allow_none=True)
    address_line1 = fields.String(allow_none=True)
    address_line2 = fields.String(allow_none=True, missing=None)
    city = fields.String(allow_none=True)
    postal_code = fields.String(allow_none=True)
    country = fields.String(allow_none=True)
    delivery_instructions = fields.String(allow_none=True, missing=None)
    notification_email = fields.String(allow_none=True, missing=None)
    is_default = fields.Boolean(allow_none=True)
    
    class Meta:
        unknown = EXCLUDE


"""Admin request/response schemas"""
from marshmallow import Schema, fields, validate, EXCLUDE
from constants.status_enums import OrderStatus, PaymentStatus


class CreateSupplierSchema(Schema):
    """Schema for creating a supplier"""
    name = fields.String(required=True, validate=validate.Length(min=1, max=255))
    contact_person = fields.String(allow_none=True, validate=validate.Length(max=255))
    phone = fields.String(allow_none=True, validate=validate.Length(max=20))
    email = fields.String(allow_none=True, validate=validate.Email())
    address = fields.String(allow_none=True)
    notes = fields.String(allow_none=True)
    is_active = fields.Boolean(missing=True)
    
    class Meta:
        unknown = EXCLUDE


class UpdateSupplierSchema(Schema):
    """Schema for updating a supplier"""
    name = fields.String(allow_none=True, validate=validate.Length(min=1, max=255))
    contact_person = fields.String(allow_none=True, validate=validate.Length(max=255))
    phone = fields.String(allow_none=True, validate=validate.Length(max=20))
    email = fields.String(allow_none=True, validate=validate.Email())
    address = fields.String(allow_none=True)
    notes = fields.String(allow_none=True)
    is_active = fields.Boolean(allow_none=True)
    
    class Meta:
        unknown = EXCLUDE


class AssignRoleSchema(Schema):
    """Schema for assigning a role to a user"""
    role = fields.String(required=True, validate=validate.OneOf(['admin', 'moderator', 'user']))
    
    class Meta:
        unknown = EXCLUDE


class UpdateOrderStatusSchema(Schema):
    """Schema for updating order status"""
    status = fields.String(required=True, validate=validate.OneOf(OrderStatus.get_all_values()))
    
    class Meta:
        unknown = EXCLUDE


class UpdateOrderPaymentSchema(Schema):
    """Schema for updating order payment status"""
    payment_status = fields.String(required=True, validate=validate.OneOf(PaymentStatus.get_all_values()))
    payment_method = fields.String(allow_none=True, validate=validate.Length(max=50))
    
    class Meta:
        unknown = EXCLUDE


class MergeOrdersSchema(Schema):
    """Schema for merging multiple orders"""
    order_ids = fields.List(fields.Integer(), required=True, validate=validate.Length(min=2))
    keep_payment_method = fields.String(allow_none=True)
    keep_delivery_method = fields.String(allow_none=True)
    keep_address_id = fields.Integer(allow_none=True)
    keep_pickup_location = fields.String(allow_none=True)
    keep_notes = fields.String(allow_none=True)
    
    class Meta:
        unknown = EXCLUDE


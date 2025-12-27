"""Order request/response schemas"""
from marshmallow import Schema, fields, validate, validates, ValidationError, post_load, EXCLUDE
from constants.status_enums import DeliveryMethod, PaymentMethod


class OrderItemSchema(Schema):
    """Schema for order item in request"""
    product_id = fields.Integer(required=True, validate=validate.Range(min=1))
    quantity = fields.Integer(required=True, validate=validate.Range(min=1))
    pricing_type = fields.String(missing='per_item', validate=validate.OneOf(['per_item', 'weight_range', 'unit_weight']))
    final_weight = fields.Float(allow_none=True, validate=validate.Range(min=0))
    
    class Meta:
        unknown = EXCLUDE


class CreateOrderSchema(Schema):
    """Schema for creating a new order"""
    group_deal_id = fields.Integer(required=True, validate=validate.Range(min=1))
    items = fields.List(fields.Nested(OrderItemSchema), required=True, validate=validate.Length(min=1))
    delivery_method = fields.String(missing=DeliveryMethod.PICKUP.value, validate=validate.OneOf(DeliveryMethod.get_all_values()))
    address_id = fields.Integer(allow_none=True, validate=validate.Range(min=1))
    pickup_location = fields.String(allow_none=True, validate=validate.Length(max=100))
    payment_method = fields.String(missing=PaymentMethod.CASH.value, validate=validate.OneOf(PaymentMethod.get_all_values()))
    notes = fields.String(allow_none=True, validate=validate.Length(max=1000))  # User custom notes
    
    @validates('items')
    def validate_items(self, value):
        if not value or len(value) == 0:
            raise ValidationError('At least one item is required')
    
    @post_load
    def validate_delivery_address(self, data, **kwargs):
        """Validate address_id is provided when delivery_method is delivery"""
        if data.get('delivery_method') == DeliveryMethod.DELIVERY.value:
            if not data.get('address_id'):
                raise ValidationError('address_id is required for delivery')
        return data
    
    class Meta:
        unknown = EXCLUDE


class UpdateOrderSchema(Schema):
    """Schema for updating an existing order"""
    items = fields.List(fields.Nested(OrderItemSchema), required=True, validate=validate.Length(min=1))
    delivery_method = fields.String(missing=DeliveryMethod.PICKUP.value, validate=validate.OneOf(DeliveryMethod.get_all_values()))
    address_id = fields.Integer(allow_none=True, validate=validate.Range(min=1))
    pickup_location = fields.String(allow_none=True, validate=validate.Length(max=100))
    payment_method = fields.String(allow_none=True, validate=validate.OneOf(PaymentMethod.get_all_values()))
    notes = fields.String(allow_none=True, validate=validate.Length(max=1000))  # User custom notes
    
    @validates('items')
    def validate_items(self, value):
        if not value or len(value) == 0:
            raise ValidationError('At least one item is required')
    
    @post_load
    def validate_delivery_address(self, data, **kwargs):
        """Validate address_id is provided when delivery_method is delivery"""
        if data.get('delivery_method') == DeliveryMethod.DELIVERY.value:
            if not data.get('address_id'):
                raise ValidationError('address_id is required for delivery')
        return data
    
    class Meta:
        unknown = EXCLUDE


class UpdateOrderWeightsSchema(Schema):
    """Schema for updating order item weights (admin only)"""
    items = fields.List(
        fields.Dict(keys=fields.Str(), values=fields.Raw()),
        required=True,
        validate=validate.Length(min=1)
    )
    
    @validates('items')
    def validate_items_structure(self, value):
        """Validate each item has item_id and final_weight"""
        for item in value:
            if 'item_id' not in item:
                raise ValidationError('Each item must have item_id')
            if 'final_weight' not in item or item['final_weight'] is None:
                raise ValidationError('Each item must have final_weight')
    
    class Meta:
        unknown = EXCLUDE


class AdminUpdateOrderSchema(Schema):
    """Schema for admin updating order items"""
    items = fields.List(fields.Nested(OrderItemSchema), required=True, validate=validate.Length(min=1))
    payment_method = fields.String(allow_none=True, validate=validate.OneOf(PaymentMethod.get_all_values()))
    
    class Meta:
        unknown = EXCLUDE


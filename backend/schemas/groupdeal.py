"""Group Deal request/response schemas"""
from marshmallow import Schema, fields, validate, validates, ValidationError, EXCLUDE
from constants.status_enums import GroupDealStatus


class GroupDealProductSchema(Schema):
    """Schema for product in a group deal"""
    product_id = fields.Integer(required=True, validate=validate.Range(min=1))
    deal_price = fields.Float(allow_none=True, validate=validate.Range(min=0))
    deal_stock_limit = fields.Integer(allow_none=True, validate=validate.Range(min=0))
    
    class Meta:
        unknown = EXCLUDE


class CreateGroupDealSchema(Schema):
    """Schema for creating a group deal"""
    title = fields.String(required=True, validate=validate.Length(min=1, max=255))
    description = fields.String(allow_none=True)
    order_start_date = fields.DateTime(required=True)
    order_end_date = fields.DateTime(required=True)
    pickup_date = fields.DateTime(required=True)
    status = fields.String(allow_none=True, validate=validate.OneOf(GroupDealStatus.get_all_values()))
    products = fields.List(fields.Nested(GroupDealProductSchema), allow_none=True)
    
    @validates('order_end_date')
    def validate_order_end_date(self, value, **kwargs):
        """Validate order_end_date is after order_start_date"""
        order_start_date = self.context.get('order_start_date')
        if order_start_date and value < order_start_date:
            raise ValidationError('order_end_date must be after order_start_date')
    
    class Meta:
        unknown = EXCLUDE


class UpdateGroupDealSchema(Schema):
    """Schema for updating a group deal"""
    title = fields.String(allow_none=True, validate=validate.Length(min=1, max=255))
    description = fields.String(allow_none=True)
    order_start_date = fields.DateTime(allow_none=True)
    order_end_date = fields.DateTime(allow_none=True)
    pickup_date = fields.DateTime(allow_none=True)
    status = fields.String(allow_none=True, validate=validate.OneOf(GroupDealStatus.get_all_values()))
    products = fields.List(fields.Nested(GroupDealProductSchema), allow_none=True)
    
    class Meta:
        unknown = EXCLUDE


class UpdateGroupDealStatusSchema(Schema):
    """Schema for updating group deal status"""
    status = fields.String(required=True, validate=validate.OneOf(GroupDealStatus.get_all_values()))
    
    class Meta:
        unknown = EXCLUDE


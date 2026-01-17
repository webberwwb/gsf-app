"""Group Deal request/response schemas"""
from marshmallow import Schema, fields, validate, validates_schema, ValidationError, EXCLUDE
from datetime import datetime
from constants.status_enums import GroupDealStatus


class DateOrDateTimeField(fields.Field):
    """Custom field that accepts both date strings (YYYY-MM-DD) and datetime strings"""
    
    def _deserialize(self, value, attr, data, **kwargs):
        """Deserialize date or datetime string to datetime object"""
        if value is None:
            return None
        
        if isinstance(value, datetime):
            return value
        
        if isinstance(value, str):
            # Check if it's a simple date string (YYYY-MM-DD)
            if len(value) == 10 and 'T' not in value:
                try:
                    # Parse as date and return as datetime at midnight
                    return datetime.strptime(value, '%Y-%m-%d')
                except ValueError:
                    raise ValidationError(f'Invalid date format: {value}. Expected YYYY-MM-DD')
            else:
                # Try to parse as ISO datetime string
                try:
                    return datetime.fromisoformat(value.replace('Z', '+00:00'))
                except ValueError:
                    raise ValidationError(f'Invalid datetime format: {value}')
        
        raise ValidationError(f'Invalid type for date/datetime field: {type(value)}')


class GroupDealProductSchema(Schema):
    """Schema for product in a group deal"""
    product_id = fields.Integer(required=True, validate=validate.Range(min=1))
    deal_stock_limit = fields.Integer(allow_none=True, validate=validate.Range(min=0))
    
    class Meta:
        unknown = EXCLUDE


class CreateGroupDealSchema(Schema):
    """Schema for creating a group deal"""
    title = fields.String(required=True, validate=validate.Length(min=1, max=255))
    description = fields.String(allow_none=True)
    order_start_date = DateOrDateTimeField(required=True)
    order_end_date = DateOrDateTimeField(required=True)
    pickup_date = DateOrDateTimeField(required=True)
    status = fields.String(allow_none=True, validate=validate.OneOf(GroupDealStatus.get_all_values()))
    products = fields.List(fields.Nested(GroupDealProductSchema), allow_none=True)
    
    @validates_schema
    def validate_dates(self, data, **kwargs):
        """Validate order_end_date is after order_start_date"""
        order_start_date = data.get('order_start_date')
        order_end_date = data.get('order_end_date')
        if order_start_date and order_end_date and order_end_date < order_start_date:
            raise ValidationError({
                'order_end_date': ['order_end_date must be after order_start_date']
            })
    
    class Meta:
        unknown = EXCLUDE


class UpdateGroupDealSchema(Schema):
    """Schema for updating a group deal"""
    title = fields.String(allow_none=True, validate=validate.Length(min=1, max=255))
    description = fields.String(allow_none=True)
    order_start_date = DateOrDateTimeField(allow_none=True)
    order_end_date = DateOrDateTimeField(allow_none=True)
    pickup_date = DateOrDateTimeField(allow_none=True)
    status = fields.String(allow_none=True, validate=validate.OneOf(GroupDealStatus.get_all_values()))
    products = fields.List(fields.Nested(GroupDealProductSchema), allow_none=True)
    
    @validates_schema
    def validate_dates(self, data, **kwargs):
        """Validate order_end_date is after order_start_date if both are provided"""
        order_start_date = data.get('order_start_date')
        order_end_date = data.get('order_end_date')
        if order_start_date and order_end_date and order_end_date < order_start_date:
            raise ValidationError({
                'order_end_date': ['order_end_date must be after order_start_date']
            })
    
    class Meta:
        unknown = EXCLUDE


class UpdateGroupDealStatusSchema(Schema):
    """Schema for updating group deal status"""
    status = fields.String(required=True, validate=validate.OneOf(GroupDealStatus.get_all_values()))
    
    class Meta:
        unknown = EXCLUDE


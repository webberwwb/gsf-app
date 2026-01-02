"""Product request/response schemas"""
from marshmallow import Schema, fields, validate, validates, ValidationError, post_load, EXCLUDE


class PricingDataPerItemSchema(Schema):
    """Schema for per_item pricing_data"""
    price = fields.Float(required=True, validate=validate.Range(min=0))


class WeightRangeSchema(Schema):
    """Schema for weight range in pricing_data"""
    min = fields.Float(required=True, validate=validate.Range(min=0))
    max = fields.Float(allow_none=True, validate=validate.Range(min=0))
    price = fields.Float(required=True, validate=validate.Range(min=0))


class PricingDataWeightRangeSchema(Schema):
    """Schema for weight_range pricing_data"""
    ranges = fields.List(fields.Nested(WeightRangeSchema), required=True, validate=validate.Length(min=1))


class PricingDataUnitWeightSchema(Schema):
    """Schema for unit_weight pricing_data"""
    price_per_unit = fields.Float(required=True, validate=validate.Range(min=0))
    unit = fields.String(missing='kg')


class PricingDataBundledWeightSchema(Schema):
    """Schema for bundled_weight pricing_data"""
    price_per_unit = fields.Float(required=True, validate=validate.Range(min=0))
    unit = fields.String(missing='lb')
    min_weight = fields.Float(required=True, validate=validate.Range(min=0))
    max_weight = fields.Float(required=True, validate=validate.Range(min=0))


class CreateProductSchema(Schema):
    """Schema for creating a product"""
    name = fields.String(required=True, validate=validate.Length(min=1, max=255))
    image = fields.String(allow_none=True, validate=validate.Length(max=512))  # Deprecated, use images
    images = fields.List(fields.String(validate=validate.Length(max=512)), allow_none=True)  # Array of image URLs
    pricing_type = fields.String(missing='per_item', validate=validate.OneOf(['per_item', 'weight_range', 'unit_weight', 'bundled_weight']))
    pricing_data = fields.Dict(required=True)
    description = fields.String(allow_none=True)
    stock_limit = fields.Integer(allow_none=True, validate=validate.Range(min=0))
    is_active = fields.Boolean(missing=True)
    supplier_id = fields.Integer(allow_none=True, validate=validate.Range(min=1))
    counts_toward_free_shipping = fields.Boolean(missing=True)
    
    @post_load
    def validate_pricing_data(self, data, **kwargs):
        """Validate pricing_data based on pricing_type"""
        pricing_type = data.get('pricing_type', 'per_item')
        pricing_data = data.get('pricing_data')
        
        if not pricing_data:
            raise ValidationError('pricing_data is required')
        
        if pricing_type == 'per_item':
            if 'price' not in pricing_data:
                raise ValidationError('pricing_data.price is required for per_item pricing')
            if not isinstance(pricing_data['price'], (int, float)) or pricing_data['price'] < 0:
                raise ValidationError('pricing_data.price must be a non-negative number')
        elif pricing_type == 'weight_range':
            if 'ranges' not in pricing_data or not isinstance(pricing_data['ranges'], list):
                raise ValidationError('pricing_data.ranges is required for weight_range pricing')
            if len(pricing_data['ranges']) == 0:
                raise ValidationError('pricing_data.ranges must contain at least one range')
            for range_item in pricing_data['ranges']:
                if 'min' not in range_item or 'price' not in range_item:
                    raise ValidationError('Each range must have min and price')
        elif pricing_type == 'unit_weight':
            if 'price_per_unit' not in pricing_data:
                raise ValidationError('pricing_data.price_per_unit is required for unit_weight pricing')
            if not isinstance(pricing_data['price_per_unit'], (int, float)) or pricing_data['price_per_unit'] < 0:
                raise ValidationError('pricing_data.price_per_unit must be a non-negative number')
        elif pricing_type == 'bundled_weight':
            if 'price_per_unit' not in pricing_data:
                raise ValidationError('pricing_data.price_per_unit is required for bundled_weight pricing')
            if not isinstance(pricing_data['price_per_unit'], (int, float)) or pricing_data['price_per_unit'] < 0:
                raise ValidationError('pricing_data.price_per_unit must be a non-negative number')
            if 'min_weight' not in pricing_data:
                raise ValidationError('pricing_data.min_weight is required for bundled_weight pricing')
            if not isinstance(pricing_data['min_weight'], (int, float)) or pricing_data['min_weight'] < 0:
                raise ValidationError('pricing_data.min_weight must be a non-negative number')
            if 'max_weight' not in pricing_data:
                raise ValidationError('pricing_data.max_weight is required for bundled_weight pricing')
            if not isinstance(pricing_data['max_weight'], (int, float)) or pricing_data['max_weight'] < 0:
                raise ValidationError('pricing_data.max_weight must be a non-negative number')
            if pricing_data['max_weight'] < pricing_data['min_weight']:
                raise ValidationError('pricing_data.max_weight must be greater than or equal to min_weight')
        
        return data
    
    class Meta:
        unknown = EXCLUDE


class UpdateProductSchema(Schema):
    """Schema for updating a product"""
    name = fields.String(allow_none=True, validate=validate.Length(min=1, max=255))
    image = fields.String(allow_none=True, validate=validate.Length(max=512))  # Deprecated, use images
    images = fields.List(fields.String(validate=validate.Length(max=512)), allow_none=True)  # Array of image URLs
    pricing_type = fields.String(allow_none=True, validate=validate.OneOf(['per_item', 'weight_range', 'unit_weight', 'bundled_weight']))
    pricing_data = fields.Dict(allow_none=True)
    description = fields.String(allow_none=True)
    stock_limit = fields.Integer(allow_none=True, validate=validate.Range(min=0))
    is_active = fields.Boolean(allow_none=True)
    supplier_id = fields.Integer(allow_none=True, validate=validate.Range(min=1))
    counts_toward_free_shipping = fields.Boolean(allow_none=True)
    
    @post_load
    def validate_pricing_data(self, data, **kwargs):
        """Validate pricing_data based on pricing_type if provided"""
        pricing_data = data.get('pricing_data')
        if pricing_data is None:
            return data
        
        # Get pricing_type from data or context (for existing product)
        pricing_type = data.get('pricing_type') or self.context.get('pricing_type')
        if not pricing_type:
            # If pricing_type not provided, skip validation (will use existing product's pricing_type)
            return data
        
        if pricing_type == 'per_item':
            if 'price' not in pricing_data:
                raise ValidationError('pricing_data.price is required for per_item pricing')
        elif pricing_type == 'weight_range':
            if 'ranges' not in pricing_data or not isinstance(pricing_data['ranges'], list) or len(pricing_data['ranges']) == 0:
                raise ValidationError('pricing_data.ranges is required for weight_range pricing')
        elif pricing_type == 'unit_weight':
            if 'price_per_unit' not in pricing_data:
                raise ValidationError('pricing_data.price_per_unit is required for unit_weight pricing')
        elif pricing_type == 'bundled_weight':
            if 'price_per_unit' not in pricing_data:
                raise ValidationError('pricing_data.price_per_unit is required for bundled_weight pricing')
            if 'min_weight' not in pricing_data:
                raise ValidationError('pricing_data.min_weight is required for bundled_weight pricing')
            if 'max_weight' not in pricing_data:
                raise ValidationError('pricing_data.max_weight is required for bundled_weight pricing')
            if pricing_data.get('max_weight', 0) < pricing_data.get('min_weight', 0):
                raise ValidationError('pricing_data.max_weight must be greater than or equal to min_weight')
        
        return data
    
    class Meta:
        unknown = EXCLUDE


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
    unit = fields.String(missing='lb')


class ProductVariantSchema(Schema):
    """Schema for a product variant (spec) option"""
    id = fields.Integer(allow_none=True, validate=validate.Range(min=1))
    name = fields.String(required=True, validate=validate.Length(min=1, max=255))
    price_delta = fields.Float(missing=0)
    sort_order = fields.Integer(missing=0, validate=validate.Range(min=0))
    is_active = fields.Boolean(missing=True)


class PricingDataBundledWeightSchema(Schema):
    """Schema for bundled_weight pricing_data"""
    price_per_unit = fields.Float(required=True, validate=validate.Range(min=0))
    unit = fields.String(missing='lb')
    min_weight = fields.Float(required=True, validate=validate.Range(min=0))
    max_weight = fields.Float(required=True, validate=validate.Range(min=0))


def validate_pricing_config(pricing_type, pricing_data, field_label='pricing_data'):
    """Validate pricing_data for a given pricing_type."""
    if not pricing_data:
        raise ValidationError(f'{field_label} is required')

    if pricing_type == 'per_item':
        if 'price' not in pricing_data:
            raise ValidationError(f'{field_label}.price is required for per_item pricing')
        if not isinstance(pricing_data['price'], (int, float)) or pricing_data['price'] < 0:
            raise ValidationError(f'{field_label}.price must be a non-negative number')
    elif pricing_type == 'weight_range':
        if 'ranges' not in pricing_data or not isinstance(pricing_data['ranges'], list):
            raise ValidationError(f'{field_label}.ranges is required for weight_range pricing')
        if len(pricing_data['ranges']) == 0:
            raise ValidationError(f'{field_label}.ranges must contain at least one range')
        for range_item in pricing_data['ranges']:
            if 'min' not in range_item or 'price' not in range_item:
                raise ValidationError('Each range must have min and price')
    elif pricing_type == 'unit_weight':
        if 'price_per_unit' not in pricing_data:
            raise ValidationError(f'{field_label}.price_per_unit is required for unit_weight pricing')
        if not isinstance(pricing_data['price_per_unit'], (int, float)) or pricing_data['price_per_unit'] < 0:
            raise ValidationError(f'{field_label}.price_per_unit must be a non-negative number')
    elif pricing_type == 'bundled_weight':
        if 'price_per_unit' not in pricing_data:
            raise ValidationError(f'{field_label}.price_per_unit is required for bundled_weight pricing')
        if not isinstance(pricing_data['price_per_unit'], (int, float)) or pricing_data['price_per_unit'] < 0:
            raise ValidationError(f'{field_label}.price_per_unit must be a non-negative number')
        if 'min_weight' not in pricing_data:
            raise ValidationError(f'{field_label}.min_weight is required for bundled_weight pricing')
        if not isinstance(pricing_data['min_weight'], (int, float)) or pricing_data['min_weight'] < 0:
            raise ValidationError(f'{field_label}.min_weight must be a non-negative number')
        if 'max_weight' not in pricing_data:
            raise ValidationError(f'{field_label}.max_weight is required for bundled_weight pricing')
        if not isinstance(pricing_data['max_weight'], (int, float)) or pricing_data['max_weight'] < 0:
            raise ValidationError(f'{field_label}.max_weight must be a non-negative number')
        if pricing_data['max_weight'] < pricing_data['min_weight']:
            raise ValidationError(f'{field_label}.max_weight must be greater than or equal to min_weight')


class CreateProductSchema(Schema):
    """Schema for creating a product"""
    name = fields.String(required=True, validate=validate.Length(min=1, max=255))
    image = fields.String(allow_none=True, validate=validate.Length(max=512))  # Deprecated, use images
    images = fields.List(fields.String(validate=validate.Length(max=512)), allow_none=True)  # Array of image URLs
    pricing_type = fields.String(missing='per_item', validate=validate.OneOf(['per_item', 'weight_range', 'unit_weight', 'bundled_weight']))
    pricing_data = fields.Dict(required=True)
    description = fields.String(allow_none=True)
    is_active = fields.Boolean(missing=True)
    supplier_id = fields.Integer(allow_none=True, validate=validate.Range(min=1))
    category_id = fields.Integer(allow_none=True, validate=validate.Range(min=1))
    counts_toward_free_shipping = fields.Boolean(missing=True)
    sort_order = fields.Integer(missing=0, validate=validate.Range(min=0))
    variants = fields.List(fields.Nested(ProductVariantSchema), allow_none=True)
    substitute_enabled = fields.Boolean(missing=False)
    substitute_name = fields.String(allow_none=True, validate=validate.Length(max=255))
    substitute_description = fields.String(allow_none=True)
    substitute_images = fields.List(fields.String(validate=validate.Length(max=512)), allow_none=True)
    substitute_price = fields.Float(allow_none=True, validate=validate.Range(min=0))  # legacy
    substitute_pricing_type = fields.String(
        allow_none=True,
        validate=validate.OneOf(['per_item', 'weight_range', 'unit_weight', 'bundled_weight']),
    )
    substitute_pricing_data = fields.Dict(allow_none=True)
    
    @validates('variants')
    def validate_variant_names_unique(self, value):
        if not value:
            return
        names = [(v.get('name') or '').strip().lower() for v in value]
        if len(names) != len(set(names)):
            raise ValidationError('Variant names must be unique')
    
    @post_load
    def validate_pricing_data(self, data, **kwargs):
        """Validate pricing_data based on pricing_type"""
        pricing_type = data.get('pricing_type', 'per_item')
        validate_pricing_config(pricing_type, data.get('pricing_data'), 'pricing_data')

        if data.get('substitute_enabled'):
            if not (data.get('substitute_name') or '').strip():
                raise ValidationError('substitute_name is required when substitute is enabled')
            sub_type = data.get('substitute_pricing_type') or pricing_type
            sub_data = data.get('substitute_pricing_data')
            if sub_type != pricing_type:
                raise ValidationError('substitute_pricing_type must match product pricing_type')
            data['substitute_pricing_type'] = sub_type
            validate_pricing_config(sub_type, sub_data, 'substitute_pricing_data')
        
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
    is_active = fields.Boolean(allow_none=True)
    supplier_id = fields.Integer(allow_none=True, validate=validate.Range(min=1))
    category_id = fields.Integer(allow_none=True, validate=validate.Range(min=1))
    counts_toward_free_shipping = fields.Boolean(allow_none=True)
    sort_order = fields.Integer(allow_none=True, validate=validate.Range(min=0))
    variants = fields.List(fields.Nested(ProductVariantSchema), allow_none=True)
    substitute_enabled = fields.Boolean(allow_none=True)
    substitute_name = fields.String(allow_none=True, validate=validate.Length(max=255))
    substitute_description = fields.String(allow_none=True)
    substitute_images = fields.List(fields.String(validate=validate.Length(max=512)), allow_none=True)
    substitute_price = fields.Float(allow_none=True, validate=validate.Range(min=0))  # legacy
    substitute_pricing_type = fields.String(
        allow_none=True,
        validate=validate.OneOf(['per_item', 'weight_range', 'unit_weight', 'bundled_weight']),
    )
    substitute_pricing_data = fields.Dict(allow_none=True)
    
    @validates('variants')
    def validate_variant_names_unique(self, value):
        if not value:
            return
        names = [(v.get('name') or '').strip().lower() for v in value]
        if len(names) != len(set(names)):
            raise ValidationError('Variant names must be unique')
    
    @post_load
    def validate_pricing_data(self, data, **kwargs):
        """Validate pricing_data based on pricing_type if provided"""
        pricing_type = data.get('pricing_type') or self.context.get('pricing_type')
        pricing_data = data.get('pricing_data')

        if pricing_data is not None and pricing_type:
            validate_pricing_config(pricing_type, pricing_data, 'pricing_data')

        if data.get('substitute_enabled'):
            if not (data.get('substitute_name') or '').strip():
                raise ValidationError('substitute_name is required when substitute is enabled')
            if not pricing_type:
                raise ValidationError('pricing_type is required when configuring substitute')
            sub_type = data.get('substitute_pricing_type') or pricing_type
            if sub_type != pricing_type:
                raise ValidationError('substitute_pricing_type must match product pricing_type')
            data['substitute_pricing_type'] = sub_type
            sub_data = data.get('substitute_pricing_data')
            if sub_data is not None:
                validate_pricing_config(sub_type, sub_data, 'substitute_pricing_data')
        
        return data
    
    class Meta:
        unknown = EXCLUDE


class UpdateProductSortOrderSchema(Schema):
    """Schema for updating product sort orders in bulk"""
    product_id = fields.Integer(required=True, validate=validate.Range(min=1))
    sort_order = fields.Integer(required=True, validate=validate.Range(min=0))
    
    class Meta:
        unknown = EXCLUDE


class BulkUpdateSortOrderSchema(Schema):
    """Schema for bulk updating product sort orders"""
    products = fields.List(fields.Nested(UpdateProductSortOrderSchema), required=True, validate=validate.Length(min=1))
    
    class Meta:
        unknown = EXCLUDE


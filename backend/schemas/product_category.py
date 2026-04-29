"""Product Category request/response schemas"""
from marshmallow import Schema, fields, validate, EXCLUDE


class CreateProductCategorySchema(Schema):
    """Schema for creating a product category"""
    name = fields.String(required=True, validate=validate.Length(min=1, max=255))
    description = fields.String(allow_none=True)
    is_active = fields.Boolean(missing=True)
    sort_order = fields.Integer(missing=0, validate=validate.Range(min=0))
    
    class Meta:
        unknown = EXCLUDE


class UpdateProductCategorySchema(Schema):
    """Schema for updating a product category"""
    name = fields.String(allow_none=True, validate=validate.Length(min=1, max=255))
    description = fields.String(allow_none=True)
    is_active = fields.Boolean(allow_none=True)
    sort_order = fields.Integer(allow_none=True, validate=validate.Range(min=0))
    
    class Meta:
        unknown = EXCLUDE


class UpdateCategorySortOrderSchema(Schema):
    """Schema for updating category sort orders in bulk"""
    category_id = fields.Integer(required=True, validate=validate.Range(min=1))
    sort_order = fields.Integer(required=True, validate=validate.Range(min=0))
    
    class Meta:
        unknown = EXCLUDE


class BulkUpdateCategorySortOrderSchema(Schema):
    """Schema for bulk updating category sort orders"""
    categories = fields.List(fields.Nested(UpdateCategorySortOrderSchema), required=True, validate=validate.Length(min=1))
    
    class Meta:
        unknown = EXCLUDE

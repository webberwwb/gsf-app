"""Work document and action item request/response schemas"""
from marshmallow import Schema, fields, validate, EXCLUDE


class CreateWorkDocumentSchema(Schema):
    """Schema for creating a work document"""
    title = fields.String(required=True, validate=validate.Length(min=1, max=500))
    content = fields.String(required=True)
    
    class Meta:
        unknown = EXCLUDE


class UpdateWorkDocumentSchema(Schema):
    """Schema for updating a work document"""
    title = fields.String(allow_none=True, validate=validate.Length(min=1, max=500))
    content = fields.String(allow_none=True)
    
    class Meta:
        unknown = EXCLUDE


class CreateActionItemSchema(Schema):
    """Schema for creating an action item"""
    document_id = fields.Integer(required=True)
    title = fields.String(required=True, validate=validate.Length(min=1, max=500))
    description = fields.String(allow_none=True)
    assigned_to_id = fields.Integer(allow_none=True)
    status = fields.String(missing='pending', validate=validate.OneOf(['pending', 'in_progress', 'completed', 'cancelled']))
    due_date = fields.DateTime(allow_none=True)
    
    class Meta:
        unknown = EXCLUDE


class UpdateActionItemSchema(Schema):
    """Schema for updating an action item"""
    title = fields.String(allow_none=True, validate=validate.Length(min=1, max=500))
    description = fields.String(allow_none=True)
    assigned_to_id = fields.Integer(allow_none=True)
    status = fields.String(allow_none=True, validate=validate.OneOf(['pending', 'in_progress', 'completed', 'cancelled']))
    due_date = fields.DateTime(allow_none=True)
    completed_at = fields.DateTime(allow_none=True)
    
    class Meta:
        unknown = EXCLUDE

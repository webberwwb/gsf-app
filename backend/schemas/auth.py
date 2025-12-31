"""Auth request/response schemas"""
from marshmallow import Schema, fields, validate, EXCLUDE


class SendOTPSchema(Schema):
    """Schema for sending OTP"""
    phone = fields.String(required=True, validate=validate.Length(min=1))
    
    class Meta:
        unknown = EXCLUDE  # Ignore unknown fields (like 'channel' which is ignored anyway)


class VerifyOTPSchema(Schema):
    """Schema for verifying OTP"""
    phone = fields.String(required=True, validate=validate.Length(min=1))
    otp = fields.String(required=True, validate=validate.Length(min=1))
    
    class Meta:
        unknown = EXCLUDE  # Ignore unknown fields


class UpdateWechatSchema(Schema):
    """Schema for updating WeChat ID and nickname"""
    wechat = fields.String(required=True, validate=validate.Length(min=1, max=255))
    nickname = fields.String(required=True, validate=validate.Length(min=1, max=255))
    
    class Meta:
        unknown = EXCLUDE


from models.base import BaseModel
from models import db
from datetime import datetime

class WorkDocument(BaseModel):
    """Work arrangement document for bi-weekly retro and planning"""
    __tablename__ = 'work_documents'
    
    title = db.Column(db.String(500), nullable=False)
    content = db.Column(db.Text, nullable=False)
    created_by_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    updated_by_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    
    created_by = db.relationship('User', foreign_keys=[created_by_id], backref='created_documents')
    updated_by = db.relationship('User', foreign_keys=[updated_by_id])
    action_items = db.relationship('ActionItem', backref='document', lazy=True, cascade='all, delete-orphan')
    
    def to_dict(self):
        data = super().to_dict()
        data.update({
            'title': self.title,
            'content': self.content,
            'created_by_id': self.created_by_id,
            'created_by': {
                'id': self.created_by.id,
                'nickname': self.created_by.nickname,
                'phone': self.created_by.phone
            } if self.created_by else None,
            'updated_by_id': self.updated_by_id,
            'updated_by': {
                'id': self.updated_by.id,
                'nickname': self.updated_by.nickname,
                'phone': self.updated_by.phone
            } if self.updated_by else None,
            'action_items_count': len(self.action_items) if self.action_items else 0
        })
        return data


class ActionItem(BaseModel):
    """Action items extracted from work documents"""
    __tablename__ = 'action_items'
    
    document_id = db.Column(db.Integer, db.ForeignKey('work_documents.id'), nullable=False, index=True)
    title = db.Column(db.String(500), nullable=False)
    description = db.Column(db.Text, nullable=True)
    assigned_to_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True, index=True)
    status = db.Column(db.String(50), default='pending', nullable=False)
    due_date = db.Column(db.DateTime, nullable=True)
    completed_at = db.Column(db.DateTime, nullable=True)
    created_by_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    
    assigned_to = db.relationship('User', foreign_keys=[assigned_to_id], backref='assigned_action_items')
    created_by = db.relationship('User', foreign_keys=[created_by_id])
    
    def to_dict(self):
        data = super().to_dict()
        data.update({
            'document_id': self.document_id,
            'title': self.title,
            'description': self.description,
            'assigned_to_id': self.assigned_to_id,
            'assigned_to': {
                'id': self.assigned_to.id,
                'nickname': self.assigned_to.nickname,
                'phone': self.assigned_to.phone
            } if self.assigned_to else None,
            'status': self.status,
            'due_date': self.due_date.isoformat() if self.due_date else None,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None,
            'created_by_id': self.created_by_id,
            'created_by': {
                'id': self.created_by.id,
                'nickname': self.created_by.nickname,
                'phone': self.created_by.phone
            } if self.created_by else None
        })
        return data

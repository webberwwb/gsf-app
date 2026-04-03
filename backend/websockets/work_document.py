from flask import request
from flask_socketio import emit, join_room, leave_room
from models import db
from models.work_document import WorkDocument
from models.user import User, AuthToken
from models.base import utc_now
from functools import wraps
from config import Config
import logging

logger = logging.getLogger(__name__)

def get_socketio():
    from app import socketio
    return socketio

def authenticate_socket(f):
    @wraps(f)
    def wrapped(data):
        token = data.get('token')
        if not token:
            logger.warning(f"WebSocket event '{f.__name__}' - No token provided")
            return {'success': False, 'error': 'Authentication required'}
        
        try:
            # Use the same authentication as REST API
            auth_token = AuthToken.query.filter_by(token=token, is_revoked=False).first()
            if not auth_token or not auth_token.is_valid():
                logger.warning(f"WebSocket event '{f.__name__}' - Invalid or expired token")
                return {'success': False, 'error': 'Invalid or expired token'}
            
            user = User.query.get(auth_token.user_id)
            if not user or not user.is_admin:
                logger.warning(f"WebSocket event '{f.__name__}' - Non-admin user {user.id if user else 'unknown'}")
                return {'success': False, 'error': 'Admin access required'}
            
            logger.info(f"WebSocket event '{f.__name__}' - Authenticated user {user.id} ({user.nickname or user.phone})")
            return f(data, user)
        except Exception as e:
            logger.error(f"WebSocket event '{f.__name__}' - Authentication failed: {str(e)}")
            return {'success': False, 'error': f'Authentication failed: {str(e)}'}
    
    return wrapped

# Store active editors {document_id: {user_id, user_name, timestamp}}
active_editors = {}

def register_websocket_handlers(socketio):
    
    @socketio.on('connect')
    def handle_connect():
        logger.info(f"Client connected: {request.sid}")
        emit('connected', {'message': 'Connected to work document server'})
    
    @socketio.on('disconnect')
    def handle_disconnect():
        logger.info(f"Client disconnected: {request.sid}")
        # Remove from active editors
        for doc_id in list(active_editors.keys()):
            if active_editors[doc_id].get('sid') == request.sid:
                user_info = active_editors.pop(doc_id)
                emit('editor_left', {
                    'document_id': doc_id,
                    'user': user_info.get('user_name')
                }, room=f'doc_{doc_id}', skip_sid=request.sid)
    
    @socketio.on('join_document')
    @authenticate_socket
    def handle_join_document(data, user):
        document_id = data.get('document_id')
        if not document_id:
            return {'success': False, 'error': 'Document ID required'}
        
        doc = WorkDocument.query.get(document_id)
        if not doc:
            return {'success': False, 'error': 'Document not found'}
        
        room = f'doc_{document_id}'
        join_room(room)
        
        # Notify others that someone joined
        emit('user_joined', {
            'user': user.nickname or user.phone,
            'user_id': user.id
        }, room=room, skip_sid=request.sid)
        
        # Send current editor info if someone is editing
        current_editor = active_editors.get(document_id)
        if current_editor:
            emit('editor_status', {
                'is_editing': True,
                'editor': current_editor.get('user_name'),
                'editor_id': current_editor.get('user_id')
            })
        
        return {'success': True, 'message': f'Joined document {document_id}'}
    
    @socketio.on('leave_document')
    def handle_leave_document(data):
        document_id = data.get('document_id')
        if document_id:
            room = f'doc_{document_id}'
            leave_room(room)
            
            # Clear editing status if this user was editing
            if document_id in active_editors and active_editors[document_id].get('sid') == request.sid:
                user_info = active_editors.pop(document_id)
                emit('editor_left', {
                    'document_id': document_id,
                    'user': user_info.get('user_name')
                }, room=room, skip_sid=request.sid)
    
    @socketio.on('start_editing')
    @authenticate_socket
    def handle_start_editing(data, user):
        document_id = data.get('document_id')
        if not document_id:
            return {'success': False, 'error': 'Document ID required'}
        
        room = f'doc_{document_id}'
        
        # Check if someone else is already editing
        current_editor = active_editors.get(document_id)
        if current_editor and current_editor.get('user_id') != user.id:
            return {
                'success': False,
                'error': f"{current_editor.get('user_name')} is currently editing this document"
            }
        
        # Mark this user as the active editor
        active_editors[document_id] = {
            'user_id': user.id,
            'user_name': user.nickname or user.phone,
            'sid': request.sid
        }
        
        # Notify others
        emit('editor_started', {
            'document_id': document_id,
            'user': user.nickname or user.phone,
            'user_id': user.id
        }, room=room, skip_sid=request.sid)
        
        return {'success': True}
    
    @socketio.on('stop_editing')
    @authenticate_socket
    def handle_stop_editing(data, user):
        document_id = data.get('document_id')
        if not document_id:
            return {'success': False, 'error': 'Document ID required'}
        
        # Clear editing status
        if document_id in active_editors and active_editors[document_id].get('user_id') == user.id:
            active_editors.pop(document_id)
            
            room = f'doc_{document_id}'
            emit('editor_stopped', {
                'document_id': document_id,
                'user': user.nickname or user.phone
            }, room=room, skip_sid=request.sid)
        
        return {'success': True}
    
    @socketio.on('typing')
    @authenticate_socket
    def handle_typing(data, user):
        document_id = data.get('document_id')
        if not document_id:
            return
        
        room = f'doc_{document_id}'
        emit('user_typing', {
            'user': user.nickname or user.phone,
            'user_id': user.id
        }, room=room, skip_sid=request.sid)
    
    @socketio.on('document_updated')
    @authenticate_socket
    def handle_document_updated(data, user):
        document_id = data.get('document_id')
        if not document_id:
            return {'success': False, 'error': 'Document ID required'}
        
        doc = WorkDocument.query.get(document_id)
        if not doc:
            return {'success': False, 'error': 'Document not found'}
        
        room = f'doc_{document_id}'
        
        # Notify all clients in the room to refresh
        emit('document_changed', {
            'document_id': document_id,
            'updated_by': user.nickname or user.phone,
            'updated_at': doc.updated_at.isoformat() if doc.updated_at else None
        }, room=room, include_self=True)
        
        return {'success': True}

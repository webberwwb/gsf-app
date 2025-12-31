from flask import Blueprint, jsonify, request, current_app, redirect
from models import db
from models.user import User, AuthToken, UserRole
from models.otp_attempt import OTPAttempt
from datetime import datetime, timedelta, timezone
from models.base import utc_now
from config import Config
from constants.status_enums import UserStatus
from schemas.auth import SendOTPSchema, VerifyOTPSchema, UpdateWechatSchema
import os
from schemas.utils import validate_request
import secrets
import requests
from twilio.rest import Client
from twilio.base.exceptions import TwilioRestException
from urllib.parse import urlencode
from decimal import Decimal

auth_bp = Blueprint('auth', __name__)

def get_twilio_client():
    """Get Twilio client instance"""
    account_sid = Config.TWILIO_ACCOUNT_SID
    auth_token = Config.TWILIO_AUTH_TOKEN
    
    if not account_sid or not auth_token:
        return None
    
    return Client(account_sid, auth_token)

def normalize_phone(phone):
    """Normalize phone number to E.164 format
    
    For Canadian/US users, automatically prepend +1 if:
    - Phone number is exactly 10 digits (no country code)
    - Phone number doesn't already start with + or 1
    """
    if not phone:
        return None
    phone = str(phone).strip()
    # Remove any non-digit characters except +
    phone = ''.join(c for c in phone if c.isdigit() or c == '+')
    
    # If exactly 10 digits, assume Canadian/US number and prepend +1
    if len(phone) == 10 and phone.isdigit():
        phone = '+1' + phone
    # If 11 digits starting with 1, add the +
    elif len(phone) == 11 and phone.startswith('1'):
        phone = '+' + phone
    # Ensure it starts with +
    elif not phone.startswith('+'):
        phone = '+' + phone.lstrip('+')
    
    return phone

@auth_bp.route('/phone/send-otp', methods=['POST'])
def phone_send_otp():
    """Send OTP via Twilio Verify (SMS only)"""
    # Validate request data using schema
    validated_data, error_response, status_code = validate_request(SendOTPSchema)
    if error_response:
        return error_response, status_code
    
    phone = validated_data['phone']
    # Always use SMS, ignore channel parameter
    channel = 'sms'
    
    # Normalize phone number
    phone = normalize_phone(phone)
    if not phone:
        return jsonify({'error': 'Invalid phone number format'}), 400
    
    # Local dev bypass: auto-login for dev phone number
    if current_app.config.get('DEBUG', False) and phone == '+19025809630':
        return jsonify({
            'message': 'Local dev mode: OTP bypassed',
            'phone': phone,
            'dev_mode': True,
            'skip_otp': True
        }), 200
    
    twilio_client = get_twilio_client()
    
    if not twilio_client:
        # Fallback to development mode
        if current_app.config.get('DEBUG', False):
            otp = str(secrets.randbelow(900000) + 100000)
            if not hasattr(current_app, 'otp_cache'):
                current_app.otp_cache = {}
            current_app.otp_cache[phone] = {
                'otp': otp,
                'expires_at': utc_now() + timedelta(minutes=5)
            }
            return jsonify({
                'message': 'OTP sent (development mode)',
                'otp': otp,  # Development only
                'phone': phone
            }), 200
        else:
            return jsonify({
                'error': 'Twilio not configured',
                'message': 'Please set TWILIO_ACCOUNT_SID and TWILIO_AUTH_TOKEN'
            }), 500
    
    try:
        # Use Twilio Verify service
        verify_service_sid = Config.TWILIO_VERIFY_SERVICE_SID
        
        current_app.logger.info(f'Sending OTP to phone: {phone} via SMS, Service SID: {verify_service_sid}')
        
        # Send OTP via SMS only
        # To customize the message, go to Twilio Console:
        # Verify → Services → [Your Service] → Messaging → Edit Template
        # You can set a custom template like:
        # "谷语农庄验证码: {{code}} (有效期5分钟，请勿分享)"
        verification = twilio_client.verify.v2.services(verify_service_sid) \
            .verifications \
            .create(to=phone, channel='sms')
        
        current_app.logger.info(f'OTP sent successfully via SMS, status: {verification.status}')
        
        # Track OTP attempt
        try:
            otp_attempt = OTPAttempt(
                phone=phone,
                action_type='send',
                status='success',
                twilio_status=verification.status,
                twilio_sid=verification.sid,
                channel='sms',
                estimated_cost=Decimal('0.0075')  # ~$0.0075 per SMS
            )
            db.session.add(otp_attempt)
            db.session.commit()
        except Exception as e:
            current_app.logger.error(f'Failed to track OTP attempt: {e}')
            db.session.rollback()
        
        return jsonify({
            'message': 'OTP sent via SMS',
            'phone': phone,
            'status': verification.status,
            'channel': 'sms'
        }), 200
        
    except TwilioRestException as e:
        error_msg = str(e.msg) if hasattr(e, 'msg') else str(e)
        error_code = e.code if hasattr(e, 'code') else None
        current_app.logger.error(f'Twilio error sending OTP: {error_msg}, code: {error_code}')
        
        # Track failed OTP attempt
        try:
            otp_attempt = OTPAttempt(
                phone=phone,
                action_type='send',
                status='failed',
                twilio_error_code=str(error_code) if error_code else None,
                twilio_error_message=error_msg,
                channel='sms',
                estimated_cost=Decimal('0')  # No cost for failed attempts
            )
            db.session.add(otp_attempt)
            db.session.commit()
        except Exception as track_error:
            current_app.logger.error(f'Failed to track failed OTP attempt: {track_error}')
            db.session.rollback()
        
        # Provide helpful error messages
        if error_code == 20404:
            error_msg = f'Verify Service not found. Check that Service SID {verify_service_sid} exists in your Twilio account.'
        elif error_code == 21211:
            error_msg = f'Invalid phone number format: {phone}. Use E.164 format (e.g., +1234567890)'
        elif error_code == 21608:
            error_msg = 'SMS delivery channel is disabled. Please enable SMS in your Twilio Verify Service settings.'
        elif error_code == 21614:
            error_msg = 'This phone number cannot receive SMS. Please verify the number is correct and can receive SMS messages.'
        
        return jsonify({
            'error': 'Failed to send OTP',
            'message': error_msg,
            'code': error_code,
            'details': {
                'phone': phone,
                'channel': channel,
                'service_sid': verify_service_sid
            }
        }), 400
    except Exception as e:
        current_app.logger.error(f'Unexpected error sending OTP: {e}', exc_info=True)
        return jsonify({
            'error': 'Unexpected error',
            'message': str(e)
        }), 500

@auth_bp.route('/phone/verify', methods=['POST'])
def phone_verify():
    """Verify phone OTP using Twilio Verify and login"""
    # Validate request data using schema
    validated_data, error_response, status_code = validate_request(VerifyOTPSchema)
    if error_response:
        return error_response, status_code
    
    phone = validated_data['phone']
    otp = validated_data['otp']
    
    # Normalize phone number first
    phone = normalize_phone(phone) if phone else None
    if not phone:
        return jsonify({'error': 'Invalid phone number format'}), 400
    
    # Local dev bypass: auto-login for dev phone number (skip OTP verification)
    skip_otp = current_app.config.get('DEBUG', False) and phone == '+19025809630'
    
    if skip_otp:
        current_app.logger.info(f'Local dev mode: Bypassing OTP for {phone}')
        # Skip OTP verification and go directly to user creation/login
    else:
        # Normalize OTP (remove spaces, ensure it's a string)
        otp = str(otp).strip().replace(' ', '').replace('-', '')
        
        twilio_client = get_twilio_client()
        
        if not twilio_client:
            # Fallback to development mode
            if current_app.config.get('DEBUG', False):
                if not hasattr(current_app, 'otp_cache'):
                    return jsonify({'error': 'OTP expired or not found'}), 400
                
                cached_otp_data = current_app.otp_cache.get(phone)
                if not cached_otp_data:
                    return jsonify({'error': 'OTP expired or not found'}), 400
                
                if utc_now() > cached_otp_data['expires_at']:
                    del current_app.otp_cache[phone]
                    return jsonify({'error': 'OTP expired'}), 400
                
                if cached_otp_data['otp'] != otp:
                    return jsonify({'error': 'Invalid OTP'}), 400
                
                del current_app.otp_cache[phone]
            else:
                return jsonify({
                    'error': 'Twilio not configured'
                }), 500
        else:
            # Verify OTP with Twilio
            try:
                verify_service_sid = Config.TWILIO_VERIFY_SERVICE_SID
                
                # Log for debugging
                current_app.logger.info(f'Verifying OTP for phone: {phone}, OTP: {otp[:2]}**, Service SID: {verify_service_sid}')
                
                verification_check = twilio_client.verify.v2.services(verify_service_sid) \
                    .verification_checks \
                    .create(to=phone, code=otp)
                
                current_app.logger.info(f'Twilio verification status: {verification_check.status}')
                
                if verification_check.status != 'approved':
                    # Track failed verification attempt
                    try:
                        otp_attempt = OTPAttempt(
                            phone=phone,
                            action_type='verify',
                            status='failed',
                            twilio_status=verification_check.status,
                            twilio_sid=verification_check.sid if hasattr(verification_check, 'sid') else None,
                            channel='sms',
                            estimated_cost=Decimal('0')
                        )
                        db.session.add(otp_attempt)
                        db.session.commit()
                    except Exception as track_error:
                        current_app.logger.error(f'Failed to track verification attempt: {track_error}')
                        db.session.rollback()
                    
                    return jsonify({
                        'error': 'Invalid or expired OTP',
                        'status': verification_check.status,
                        'message': f'Verification status: {verification_check.status}. Please check your OTP and try again.'
                    }), 400
                    
            except TwilioRestException as e:
                current_app.logger.error(f'Twilio verification error: {e}')
                error_msg = str(e.msg) if hasattr(e, 'msg') else str(e)
                error_code = e.code if hasattr(e, 'code') else None
                
                # Track failed verification attempt
                try:
                    otp_attempt = OTPAttempt(
                        phone=phone,
                        action_type='verify',
                        status='failed',
                        twilio_error_code=str(error_code) if error_code else None,
                        twilio_error_message=error_msg,
                        channel='sms',
                        estimated_cost=Decimal('0')
                    )
                    db.session.add(otp_attempt)
                    db.session.commit()
                except Exception as track_error:
                    current_app.logger.error(f'Failed to track verification error: {track_error}')
                    db.session.rollback()
                
                return jsonify({
                    'error': 'Verification failed',
                    'message': error_msg,
                    'code': error_code
                }), 400
            except Exception as e:
                current_app.logger.error(f'Unexpected verification error: {e}')
                return jsonify({
                    'error': 'Unexpected error',
                    'message': str(e)
                }), 500
    
    # OTP verified (or bypassed in dev mode), find or create user by phone number
    # Try exact match first
    user = User.query.filter_by(phone=phone).first()
    
    # If not found, try with different phone formats (backward compatibility)
    if not user:
        # Try without + prefix
        phone_alt = phone.lstrip('+')
        user = User.query.filter_by(phone=phone_alt).first()
        if user:
            # Update to normalized format
            user.phone = phone
    
    # Create new user if not found
    if not user:
        try:
            # Special handling for dev user
            if skip_otp and phone == '+19025809630':
                nickname = 'Weibo'
                points = 10000
            else:
                nickname = None
                points = 0
            
            user = User(
                phone=phone,
                nickname=nickname,
                points=points,
                status=UserStatus.ACTIVE.value
            )
            db.session.add(user)
            db.session.flush()  # Flush to get user.id
            current_app.logger.info(f'Created new user with phone: {phone}, ID: {user.id}, nickname: {nickname}, points: {points}')
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f'Error creating user: {e}')
            return jsonify({
                'error': 'Failed to create user',
                'message': str(e)
            }), 500
    else:
        # Update existing user
        # Update phone number if changed
        if not user.phone or user.phone != phone:
            user.phone = phone
        
        # Update dev user if in dev mode
        if skip_otp and phone == '+19025809630':
            if not user.nickname or user.nickname != 'Weibo':
                user.nickname = 'Weibo'
            if user.points < 10000:
                user.points = 10000
        
        user.last_login_date = utc_now()
        current_app.logger.info(f'Found existing user with phone: {phone}, ID: {user.id}, nickname: {user.nickname}, points: {user.points}')
    
    # Ensure last_login_date is set
    if not user.last_login_date:
        user.last_login_date = utc_now()
    
    db.session.commit()
    
    # Track successful verification attempt (only if OTP was actually verified, not dev bypass)
    if not skip_otp:
        try:
            otp_attempt = OTPAttempt(
                phone=phone,
                action_type='verify',
                status='success',
                channel='sms',
                estimated_cost=Decimal('0'),  # Verification is free
                user_id=user.id
            )
            db.session.add(otp_attempt)
            db.session.commit()
        except Exception as track_error:
            current_app.logger.error(f'Failed to track successful verification: {track_error}')
            db.session.rollback()
    
    # Generate new auth token (30 days expiration - 1 month)
    # Store as naive datetime (MySQL doesn't support timezone-aware)
    expires_at = utc_now() + timedelta(days=30)
    auth_token = AuthToken(
        user_id=user.id,
        token=secrets.token_urlsafe(32),
        token_type='bearer',
        expires_at=expires_at  # Already naive datetime
    )
    db.session.add(auth_token)
    db.session.commit()
    
    current_app.logger.info(f'Generated auth token for user {user.id}, token: {auth_token.token[:10]}...')
    
    return jsonify({
        'token': auth_token.token,
        'user': user.to_dict(),
        'expires_at': auth_token.expires_at.isoformat()
    }), 200

@auth_bp.route('/me', methods=['GET'])
def get_current_user():
    """Get current authenticated user"""
    try:
        # Extract token from Authorization header
        auth_header = request.headers.get('Authorization', '')
        if auth_header.startswith('Bearer '):
            token = auth_header.replace('Bearer ', '').strip()
        else:
            token = auth_header.strip()
        
        if not token:
            return jsonify({'error': 'No token provided'}), 401
        
        # Find valid auth token
        auth_token = AuthToken.query.filter_by(token=token, is_revoked=False).first()
        
        if not auth_token:
            return jsonify({'error': 'Invalid token'}), 401
        
        if not auth_token.is_valid():
            return jsonify({'error': 'Token expired'}), 401
        
        # Refresh token expiration on each use (extend to 30 days from now)
        # This ensures if user uses app at least once a month, they never need to OTP again
        # Make sure expires_at is stored as naive datetime (MySQL doesn't support timezone-aware)
        new_expires_at = utc_now() + timedelta(days=30)
        # Already naive UTC datetime for database storage
        auth_token.expires_at = new_expires_at
        db.session.commit()
        
        # Get user
        user = User.query.get(auth_token.user_id)
        
        if not user:
            return jsonify({'error': 'User not found'}), 401
        
        if not user.is_active:
            return jsonify({'error': 'User account is inactive'}), 403
        
        return jsonify({
            'user': user.to_dict(),
            'token': {
                'expires_at': auth_token.expires_at.isoformat(),
                'token_type': auth_token.token_type
            }
        }), 200
    except Exception as e:
        current_app.logger.error(f'Error in /me endpoint: {e}', exc_info=True)
        return jsonify({
            'error': 'Internal server error',
            'message': str(e)
        }), 500

@auth_bp.route('/logout', methods=['POST'])
def logout():
    """Logout and revoke token"""

    # Extract token from Authorization header
    auth_header = request.headers.get('Authorization', '')
    if auth_header.startswith('Bearer '):
        token = auth_header.replace('Bearer ', '').strip()
    else:
        token = auth_header.strip()

    if token:
        auth_token = AuthToken.query.filter_by(token=token).first()
        if auth_token:
            auth_token.is_revoked = True
            db.session.commit()
            current_app.logger.info(f'Revoked token for user {auth_token.user_id}')

    return jsonify({'message': 'Logged out successfully'}), 200

@auth_bp.route('/me/wechat', methods=['PUT'])
def update_wechat():
    """Update current user's WeChat ID"""
    try:
        # Extract token from Authorization header
        auth_header = request.headers.get('Authorization', '')
        if auth_header.startswith('Bearer '):
            token = auth_header.replace('Bearer ', '').strip()
        else:
            token = auth_header.strip()
        
        if not token:
            return jsonify({'error': 'No token provided'}), 401
        
        # Find valid auth token
        auth_token = AuthToken.query.filter_by(token=token, is_revoked=False).first()
        
        if not auth_token:
            return jsonify({'error': 'Invalid token'}), 401
        
        if not auth_token.is_valid():
            return jsonify({'error': 'Token expired'}), 401
        
        # Get user
        user = User.query.get(auth_token.user_id)
        
        if not user:
            return jsonify({'error': 'User not found'}), 401
        
        if not user.is_active:
            return jsonify({'error': 'User account is inactive'}), 403
        
        # Validate request data
        validated_data, error_response, status_code = validate_request(UpdateWechatSchema)
        if error_response:
            return error_response, status_code
        
        # Update wechat
        user.wechat = validated_data['wechat']
        
        # Update nickname (required)
        user.nickname = validated_data['nickname'].strip()
        
        db.session.commit()
        
        current_app.logger.info(f'Updated wechat and nickname for user {user.id}')
        
        return jsonify({
            'user': user.to_dict(),
            'message': '个人信息更新成功'
        }), 200
    except Exception as e:
        current_app.logger.error(f'Error updating wechat: {e}', exc_info=True)
        db.session.rollback()
        return jsonify({
            'error': 'Internal server error',
            'message': str(e)
        }), 500

# Google OAuth routes for Admin
@auth_bp.route('/google/login-url', methods=['GET'])
def google_login_url():
    """Get Google OAuth login URL"""
    client_id = Config.GOOGLE_OAUTH_CLIENT_ID
    
    if not client_id:
        return jsonify({'error': 'Google OAuth not configured', 'message': 'GOOGLE_OAUTH_CLIENT_ID is not set'}), 500
    
    # Use config redirect_uri (set in .env for local, env var for prod)
    redirect_uri = Config.GOOGLE_OAUTH_REDIRECT_URI
    
    params = {
        'client_id': client_id,
        'redirect_uri': redirect_uri,
        'response_type': 'code',
        'scope': 'openid email profile',
        'access_type': 'offline',
        'prompt': 'consent'
    }
    auth_url = f"https://accounts.google.com/o/oauth2/v2/auth?{urlencode(params)}"
    
    return jsonify({'auth_url': auth_url}), 200

@auth_bp.route('/google/callback', methods=['GET', 'POST'])
def google_callback():
    """Handle Google OAuth callback"""
    code = request.args.get('code')
    error = request.args.get('error')
    
    # Use config redirect_uri (set in .env for local, env var for prod)
    redirect_uri = Config.GOOGLE_OAUTH_REDIRECT_URI
    
    if error:
        return jsonify({'error': 'OAuth error', 'message': error}), 400
    
    if not code:
        return jsonify({'error': 'Missing authorization code'}), 400
    
    client_id = Config.GOOGLE_OAUTH_CLIENT_ID
    client_secret = Config.GOOGLE_OAUTH_CLIENT_SECRET
    
    if not client_id or not client_secret:
        return jsonify({'error': 'Google OAuth not configured'}), 500
    
    # Exchange code for token
    try:
        token_response = requests.post('https://oauth2.googleapis.com/token', data={
            'code': code,
            'client_id': client_id,
            'client_secret': client_secret,
            'redirect_uri': redirect_uri,
            'grant_type': 'authorization_code'
        })
        
        if not token_response.ok:
            current_app.logger.error(f'Token exchange failed: {token_response.text}')
            return jsonify({
                'error': 'OAuth request failed',
                'message': token_response.text
            }), 400
        
        tokens = token_response.json()
        
        access_token = tokens.get('access_token')
        id_token = tokens.get('id_token')
        
        if not access_token:
            return jsonify({
                'error': 'Failed to get access token'
            }), 400
        
        # Get user info from Google
        userinfo_url = 'https://www.googleapis.com/oauth2/v2/userinfo'
        headers = {'Authorization': f'Bearer {access_token}'}
        userinfo_response = requests.get(userinfo_url, headers=headers)
        userinfo_response.raise_for_status()
        google_user = userinfo_response.json()
        
        email = google_user.get('email')
        name = google_user.get('name', '')
        picture = google_user.get('picture', '')
        google_id = google_user.get('id')
        
        if not email:
            return jsonify({
                'error': 'Failed to get user email from Google'
            }), 400
        
        # Check email allowlist
        from urllib.parse import quote
        admin_allowed_emails = Config.ADMIN_ALLOWED_EMAILS
        admin_domains = Config.ADMIN_ALLOWED_DOMAINS
        
        # Get frontend URL from config (set in .env for local, env var for prod)
        frontend_url = Config.ADMIN_FRONTEND_URL
        
        # Ensure we're using the correct frontend URL (never localhost in production)
        if not frontend_url or 'localhost' in frontend_url.lower():
            current_app.logger.error(f'Invalid ADMIN_FRONTEND_URL: {frontend_url}. Using default.')
            frontend_url = 'https://admin.grainstoryfarm.ca'
        
        if admin_allowed_emails:
            if email.lower() not in [e.lower() for e in admin_allowed_emails]:
                error_message = 'Your email address is not authorized for admin access. Please contact an administrator.'
                return redirect(f'{frontend_url}/login?error={quote(error_message)}')
        elif admin_domains:
            email_domain = email.split('@')[1] if '@' in email else ''
            if email_domain not in admin_domains:
                error_message = f'Email domain {email_domain} is not authorized for admin access'
                return redirect(f'{frontend_url}/login?error={quote(error_message)}')
        
        # Find or create user
        user = User.query.filter_by(email=email).first()

        if not user:
            # Create new admin user
            user = User(
                email=email,
                nickname=name,
                phone=None,  # Google OAuth users don't need phone
                status=UserStatus.ACTIVE.value,
                points=0
            )
            db.session.add(user)
            db.session.flush()
            current_app.logger.info(f'Created new admin user: {email}, ID: {user.id}')
        else:
            # Update existing user
            if name and not user.nickname:
                user.nickname = name
            user.last_login_date = utc_now()
            current_app.logger.info(f'Found existing admin user: {email}, ID: {user.id}')

        # Ensure last_login_date is set
        if not user.last_login_date:
            user.last_login_date = utc_now()

        # Ensure user has admin role
        admin_role = UserRole.query.filter_by(user_id=user.id, role='admin').first()
        if not admin_role:
            admin_role = UserRole(user_id=user.id, role='admin')
            db.session.add(admin_role)
            current_app.logger.info(f'Assigned admin role to user: {email}, ID: {user.id}')

        db.session.commit()
        
        # Generate auth token (30 days expiration - 1 month)
        # Store as naive datetime (MySQL doesn't support timezone-aware)
        expires_at = utc_now() + timedelta(days=30)
        auth_token = AuthToken(
            user_id=user.id,
            token=secrets.token_urlsafe(32),
            token_type='google',
            expires_at=expires_at  # Already naive datetime
        )
        db.session.add(auth_token)
        db.session.commit()
        
        # Always redirect to admin frontend with token
        # Get frontend URL from config (set in .env for local, env var for prod)
        frontend_url = Config.ADMIN_FRONTEND_URL
        
        # Log for debugging
        current_app.logger.info(f'Redirecting to admin frontend: {frontend_url}/login#token={auth_token.token[:10]}...')
        
        # Only enforce production URL if we're running on Cloud Run (production)
        # Allow localhost for local development
        is_production = os.environ.get('K_SERVICE') is not None
        if is_production:
            # In production, never allow localhost
            if not frontend_url or 'localhost' in frontend_url.lower():
                current_app.logger.error(f'Invalid ADMIN_FRONTEND_URL in production: {frontend_url}. Using default.')
                frontend_url = 'https://admin.grainstoryfarm.ca'
        else:
            # In local development, use localhost if ADMIN_FRONTEND_URL is not set or is production URL
            if not frontend_url or 'grainstoryfarm.ca' in frontend_url:
                frontend_url = 'http://localhost:3001'  # Admin frontend dev server port
                current_app.logger.info(f'Using default localhost URL for local development: {frontend_url}')
        
        return redirect(f'{frontend_url}/login#token={auth_token.token}&user={user.id}')
        
    except requests.exceptions.RequestException as e:
        current_app.logger.error(f'Google OAuth request error: {e}')
        return jsonify({
            'error': 'OAuth request failed',
            'message': str(e)
        }), 500
    except Exception as e:
        current_app.logger.error(f'Unexpected error in Google OAuth callback: {e}', exc_info=True)
        return jsonify({
            'error': 'Unexpected error',
            'message': str(e)
        }), 500


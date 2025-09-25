"""
Enterprise security features
"""
from typing import Optional, Dict, Any
from datetime import datetime, timedelta
from fastapi import HTTPException, Security, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError, jwt
from passlib.context import CryptContext
import secrets
from sqlalchemy.orm import Session
from src.models.database import User, Organization, ApiKey, AuditLog
from src.core.config import settings
from src.utils.logger import logger
import ipaddress

class SecurityManager:
    """Handles authentication and authorization"""
    
    def __init__(self):
        self.pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
        self.security = HTTPBearer()
        self.secret_key = settings.secret_key
        self.algorithm = "HS256"
        self.access_token_expire = timedelta(minutes=30)
        
        # IP whitelist cache
        self.ip_whitelist_cache: Dict[str, set] = {}
        
    def create_access_token(self, data: dict) -> str:
        """Create JWT access token"""
        to_encode = data.copy()
        expire = datetime.utcnow() + self.access_token_expire
        
        to_encode.update({
            "exp": expire,
            "iat": datetime.utcnow(),
            "jti": secrets.token_urlsafe(16)  # JWT ID for revocation
        })
        
        encoded_jwt = jwt.encode(
            to_encode,
            self.secret_key,
            algorithm=self.algorithm
        )
        
        return encoded_jwt
    
    def verify_token(self, token: str) -> Dict[str, Any]:
        """Verify JWT token"""
        try:
            payload = jwt.decode(
                token,
                self.secret_key,
                algorithms=[self.algorithm]
            )
            return payload
        except JWTError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication credentials"
            )
    
    def verify_api_key(
        self,
        credentials: HTTPAuthorizationCredentials = Security(HTTPBearer()),
        db: Session = Depends(get_db),
        request: Request = None
    ) -> Organization:
        """Verify API key and return organization"""
        api_key = credentials.credentials
        
        # Check if API key exists and is active
        key_record = db.query(ApiKey).filter(
            ApiKey.key == api_key,
            ApiKey.is_active == True
        ).first()
        
        if not key_record:
            # Log failed attempt
            self.log_security_event(
                db,
                "api_key_invalid",
                {"api_key": api_key[:10] + "..."},
                request
            )
            
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid API key"
            )
        
        # Check expiration
        if key_record.expires_at and key_record.expires_at < datetime.utcnow():
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="API key expired"
            )
        
        # Check IP whitelist
        if request and not self.check_ip_whitelist(key_record.organization_id, request.client.host):
            self.log_security_event(
                db,
                "ip_not_whitelisted",
                {"ip": request.client.host},
                request
            )
            
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="IP address not whitelisted"
            )
        
        # Update last used
        key_record.last_used_at = datetime.utcnow()
        key_record.usage_count += 1
        db.commit()
        
        return key_record.organization
    
    def check_ip_whitelist(self, org_id: int, ip: str) -> bool:
        """Check if IP is whitelisted for organization"""
        # Check cache
        if org_id in self.ip_whitelist_cache:
            whitelist = self.ip_whitelist_cache[org_id]
            
            # Check exact match or network match
            for allowed_ip in whitelist:
                try:
                    if '/' in allowed_ip:
                        # Network notation
                        if ipaddress.ip_address(ip) in ipaddress.ip_network(allowed_ip):
                            return True
                    elif ip == allowed_ip:
                        return True
                except:
                    continue
            
            return False
        
        # No whitelist means all IPs allowed
        return True
    
    def hash_password(self, password: str) -> str:
        """Hash password using bcrypt"""
        return self.pwd_context.hash(password)
    
    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """Verify password against hash"""
        return self.pwd_context.verify(plain_password, hashed_password)
    
    def log_security_event(
        self,
        db: Session,
        event_type: str,
        details: Dict[str, Any],
        request: Request = None
    ):
        """Log security events for audit"""
        log = AuditLog(
            event_type=event_type,
            details=json.dumps(details),
            ip_address=request.client.host if request else None,
            user_agent=request.headers.get('user-agent') if request else None,
            timestamp=datetime.utcnow()
        )
        
        db.add(log)
        db.commit()
        
        # Alert on suspicious events
        if event_type in ['api_key_invalid', 'ip_not_whitelisted', 'rate_limit_exceeded']:
            logger.warning(f"Security event: {event_type} - {details}")
    
    def generate_api_key(self, org_id: int, name: str, expires_days: int = 365) -> str:
        """Generate new API key for organization"""
        # Generate cryptographically secure key
        key = f"wfa_{secrets.token_urlsafe(32)}"
        
        # Store hashed version
        key_hash = self.hash_password(key)
        
        return key
    
    def rotate_api_key(self, db: Session, old_key: str) -> str:
        """Rotate API key"""
        # Find existing key
        key_record = db.query(ApiKey).filter(
            ApiKey.key == old_key
        ).first()
        
        if not key_record:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="API key not found"
            )
        
        # Deactivate old key
        key_record.is_active = False
        key_record.revoked_at = datetime.utcnow()
        
        # Generate new key
        new_key = self.generate_api_key(
            key_record.organization_id,
            f"{key_record.name} (rotated)"
        )
        
        # Create new key record
        new_key_record = ApiKey(
            organization_id=key_record.organization_id,
            key=new_key,
            name=f"{key_record.name} (rotated)",
            created_at=datetime.utcnow(),
            expires_at=datetime.utcnow() + timedelta(days=365),
            is_active=True
        )
        
        db.add(new_key_record)
        db.commit()
        
        # Log rotation
        self.log_security_event(
            db,
            "api_key_rotated",
            {"old_key": old_key[:10] + "...", "new_key": new_key[:10] + "..."}
        )
        
        return new_key

# Global security manager
security_manager = SecurityManager()

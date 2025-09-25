"""
Multi-tenancy support for enterprise deployment
"""
from typing import Dict, Any, Optional
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from src.models.database import Organization, OrganizationSettings, UsageStats
from src.utils.logger import logger
from src.core.config import settings
import hashlib
import secrets

class TenantManager:
    """Manages multi-tenant operations"""
    
    def __init__(self):
        self.tenant_cache: Dict[str, Dict[str, Any]] = {}
        self.rate_limits = {
            'starter': {'emails_per_hour': 100, 'api_calls_per_minute': 60},
            'professional': {'emails_per_hour': 1000, 'api_calls_per_minute': 300},
            'enterprise': {'emails_per_hour': 10000, 'api_calls_per_minute': 1000}
        }
    
    def create_organization(
        self,
        db: Session,
        name: str,
        domain: str,
        plan: str = 'starter'
    ) -> Organization:
        """Create new organization"""
        # Generate API key
        api_key = self.generate_api_key()
        
        # Create organization
        org = Organization(
            name=name,
            domain=domain,
            plan=plan,
            api_key=api_key,
            created_at=datetime.utcnow()
        )
        
        db.add(org)
        
        # Create default settings
        settings = OrganizationSettings(
            organization_id=org.id,
            email_signature="Best regards,\n{org_name} Team",
            auto_response_enabled=True,
            working_hours_start="09:00",
            working_hours_end="17:00",
            timezone="UTC"
        )
        
        db.add(settings)
        db.commit()
        
        logger.info(f"Created organization: {name}")
        return org
    
    def generate_api_key(self) -> str:
        """Generate secure API key"""
        # Generate random bytes
        random_bytes = secrets.token_bytes(32)
        
        # Create hash
        api_key = hashlib.sha256(random_bytes).hexdigest()
        
        # Add prefix for easy identification
        return f"wfa_{api_key}"
    
    def validate_api_key(self, db: Session, api_key: str) -> Optional[Organization]:
        """Validate API key and return organization"""
        # Check cache first
        if api_key in self.tenant_cache:
            cached = self.tenant_cache[api_key]
            if cached['expires'] > datetime.utcnow():
                return cached['organization']
        
        # Query database
        org = db.query(Organization).filter(
            Organization.api_key == api_key,
            Organization.is_active == True
        ).first()
        
        if org:
            # Cache for 5 minutes
            self.tenant_cache[api_key] = {
                'organization': org,
                'expires': datetime.utcnow() + timedelta(minutes=5)
            }
        
        return org
    
    def check_rate_limit(
        self,
        db: Session,
        org: Organization,
        action: str
    ) -> tuple[bool, Optional[str]]:
        """Check if organization has exceeded rate limits"""
        limits = self.rate_limits.get(org.plan, self.rate_limits['starter'])
        
        # Get current usage
        now = datetime.utcnow()
        
        if action == 'email_processing':
            # Check hourly email limit
            hour_ago = now - timedelta(hours=1)
            
            email_count = db.query(UsageStats).filter(
                UsageStats.organization_id == org.id,
                UsageStats.action == 'email_processed',
                UsageStats.timestamp >= hour_ago
            ).count()
            
            if email_count >= limits['emails_per_hour']:
                return False, f"Hourly email limit exceeded ({limits['emails_per_hour']} emails/hour)"
        
        elif action == 'api_call':
            # Check per-minute API limit
            minute_ago = now - timedelta(minutes=1)
            
            api_count = db.query(UsageStats).filter(
                UsageStats.organization_id == org.id,
                UsageStats.action == 'api_call',
                UsageStats.timestamp >= minute_ago
            ).count()
            
            if api_count >= limits['api_calls_per_minute']:
                return False, f"API rate limit exceeded ({limits['api_calls_per_minute']} calls/minute)"
        
        # Log usage
        usage = UsageStats(
            organization_id=org.id,
            action=action,
            timestamp=now
        )
        db.add(usage)
        db.commit()
        
        return True, None
    
    def get_organization_stats(
        self,
        db: Session,
        org: Organization,
        days: int = 30
    ) -> Dict[str, Any]:
        """Get organization usage statistics"""
        since = datetime.utcnow() - timedelta(days=days)
        
        # Email statistics
        email_stats = db.query(
            UsageStats.action,
            func.count(UsageStats.id).label('count')
        ).filter(
            UsageStats.organization_id == org.id,
            UsageStats.timestamp >= since,
            UsageStats.action.in_(['email_processed', 'email_failed'])
        ).group_by(UsageStats.action).all()
        
        # API statistics
        api_calls = db.query(func.count(UsageStats.id)).filter(
            UsageStats.organization_id == org.id,
            UsageStats.timestamp >= since,
            UsageStats.action == 'api_call'
        ).scalar()
        
        # Calculate costs (example pricing)
        cost_per_email = 0.001 if org.plan == 'enterprise' else 0.002
        total_emails = sum(stat.count for stat in email_stats if stat.action == 'email_processed')
        estimated_cost = total_emails * cost_per_email
        
        return {
            'organization': org.name,
            'plan': org.plan,
            'period_days': days,
            'emails_processed': total_emails,
            'api_calls': api_calls,
            'estimated_cost': round(estimated_cost, 2),
            'limits': self.rate_limits.get(org.plan)
        }

# Global tenant manager
tenant_manager = TenantManager()

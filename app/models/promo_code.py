"""Promo Code Model for early adopter discounts and marketing campaigns"""

from datetime import datetime
from app import db


class PromoCode(db.Model):
    """Promo codes for discounts and special offers"""
    
    __tablename__ = 'promo_codes'
    __table_args__ = (
        db.Index('idx_promo_codes_code', 'code'),
        db.Index('idx_promo_codes_active', 'is_active'),
    )
    
    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(50), unique=True, nullable=False, index=True)
    description = db.Column(db.String(200), nullable=True)
    
    # Discount settings
    discount_type = db.Column(db.String(20), nullable=False, default='percent')  # 'percent' or 'fixed'
    discount_value = db.Column(db.Numeric(10, 2), nullable=False)  # Percentage (e.g., 20.00 for 20%) or fixed amount
    duration = db.Column(db.String(20), nullable=False, default='once')  # 'once', 'repeating', 'forever'
    duration_in_months = db.Column(db.Integer, nullable=True)  # For 'repeating' duration
    
    # Usage limits
    max_redemptions = db.Column(db.Integer, nullable=True)  # Null = unlimited
    times_redeemed = db.Column(db.Integer, default=0, nullable=False)
    
    # Validity period
    valid_from = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    valid_until = db.Column(db.DateTime, nullable=True)  # Null = no expiry
    
    # Status
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    
    # Stripe integration
    stripe_coupon_id = db.Column(db.String(100), nullable=True)  # Stripe coupon ID if synced
    stripe_promotion_code_id = db.Column(db.String(100), nullable=True)  # Stripe promotion code ID
    
    # Restrictions
    first_time_only = db.Column(db.Boolean, default=False, nullable=False)  # Only for new customers
    min_seats = db.Column(db.Integer, nullable=True)  # Minimum seats required
    max_seats = db.Column(db.Integer, nullable=True)  # Maximum seats allowed
    plan_restrictions = db.Column(db.String(200), nullable=True)  # Comma-separated plan IDs
    
    # Metadata
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    
    # Relationships
    redemptions = db.relationship('PromoCodeRedemption', back_populates='promo_code', lazy='dynamic')
    
    def __repr__(self):
        return f'<PromoCode {self.code}>'
    
    @property
    def is_valid(self):
        """Check if promo code is currently valid"""
        now = datetime.utcnow()
        
        # Check if active
        if not self.is_active:
            return False
        
        # Check validity period
        if self.valid_from and now < self.valid_from:
            return False
        if self.valid_until and now > self.valid_until:
            return False
        
        # Check redemption limits
        if self.max_redemptions and self.times_redeemed >= self.max_redemptions:
            return False
        
        return True
    
    def can_be_used_by(self, organization):
        """Check if promo code can be used by a specific organization"""
        if not self.is_valid:
            return False, "Promo code is not valid"
        
        # Check if first-time only
        if self.first_time_only:
            if hasattr(organization, 'stripe_subscription_id') and organization.stripe_subscription_id:
                return False, "This promo code is only for new customers"
        
        # Check if already used by this organization
        existing_redemption = PromoCodeRedemption.query.filter_by(
            promo_code_id=self.id,
            organization_id=organization.id
        ).first()
        if existing_redemption:
            return False, "This promo code has already been used by your organization"
        
        return True, "Promo code is valid"
    
    def redeem(self, organization_id, user_id=None):
        """Redeem the promo code for an organization"""
        redemption = PromoCodeRedemption(
            promo_code_id=self.id,
            organization_id=organization_id,
            redeemed_by=user_id,
            redeemed_at=datetime.utcnow()
        )
        
        self.times_redeemed += 1
        
        db.session.add(redemption)
        db.session.commit()
        
        return redemption
    
    def get_discount_description(self):
        """Get human-readable discount description"""
        if self.discount_type == 'percent':
            discount = f"{int(self.discount_value)}% off"
        else:
            discount = f"€{self.discount_value} off"
        
        if self.duration == 'once':
            duration = "first payment"
        elif self.duration == 'forever':
            duration = "forever"
        elif self.duration == 'repeating':
            duration = f"{self.duration_in_months} months"
        else:
            duration = ""
        
        return f"{discount} for {duration}" if duration else discount


class PromoCodeRedemption(db.Model):
    """Track promo code redemptions"""
    
    __tablename__ = 'promo_code_redemptions'
    __table_args__ = (
        db.Index('idx_redemptions_promo_code', 'promo_code_id'),
        db.Index('idx_redemptions_org', 'organization_id'),
    )
    
    id = db.Column(db.Integer, primary_key=True)
    promo_code_id = db.Column(db.Integer, db.ForeignKey('promo_codes.id'), nullable=False)
    organization_id = db.Column(db.Integer, db.ForeignKey('organizations.id'), nullable=False)
    redeemed_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    redeemed_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    
    # Stripe info
    stripe_subscription_id = db.Column(db.String(100), nullable=True)
    
    # Relationships
    promo_code = db.relationship('PromoCode', back_populates='redemptions')
    organization = db.relationship('Organization')
    user = db.relationship('User')
    
    def __repr__(self):
        return f'<PromoCodeRedemption {self.promo_code_id} by org {self.organization_id}>'


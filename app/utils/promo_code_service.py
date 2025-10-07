"""Promo Code Service for handling discounts and promotions"""

import stripe
from typing import Optional, Dict, Any, Tuple
from flask import current_app
from app import db
from app.models.promo_code import PromoCode, PromoCodeRedemption
from app.models.organization import Organization


class PromoCodeService:
    """Service for managing promo codes and Stripe coupons"""
    
    def __init__(self):
        """Initialize promo code service"""
        self._initialized = False
    
    def _ensure_initialized(self):
        """Ensure Stripe is initialized"""
        if not self._initialized:
            try:
                api_key = current_app.config.get('STRIPE_SECRET_KEY')
                if api_key:
                    stripe.api_key = api_key
                self._initialized = True
            except RuntimeError:
                pass
    
    def validate_promo_code(self, code: str, organization: Organization = None) -> Tuple[bool, Optional[PromoCode], str]:
        """Validate a promo code
        
        Args:
            code: Promo code string
            organization: Organization trying to use the code (optional)
        
        Returns:
            Tuple of (is_valid, promo_code_object, message)
        """
        # Find promo code
        promo_code = PromoCode.query.filter_by(code=code.upper()).first()
        
        if not promo_code:
            return False, None, "Promo code not found"
        
        if not promo_code.is_valid:
            return False, promo_code, "Promo code is expired or has reached its usage limit"
        
        # Check organization-specific restrictions if provided
        if organization:
            can_use, message = promo_code.can_be_used_by(organization)
            if not can_use:
                return False, promo_code, message
        
        return True, promo_code, "Promo code is valid"
    
    def apply_promo_code(self, code: str, organization: Organization, user_id: int = None) -> Tuple[bool, Optional[str], str]:
        """Apply a promo code to an organization
        
        Args:
            code: Promo code string
            organization: Organization to apply code to
            user_id: User who is applying the code (optional)
        
        Returns:
            Tuple of (success, stripe_coupon_id, message)
        """
        # Validate code
        is_valid, promo_code, message = self.validate_promo_code(code, organization)
        
        if not is_valid:
            return False, None, message
        
        try:
            # Sync with Stripe if not already synced
            if not promo_code.stripe_coupon_id:
                self._sync_to_stripe(promo_code)
            
            # Record redemption
            redemption = promo_code.redeem(
                organization_id=organization.id,
                user_id=user_id
            )
            
            # Update organization with promo code info
            organization.promo_code = promo_code.code
            organization.promo_code_applied_at = redemption.redeemed_at
            db.session.commit()
            
            return True, promo_code.stripe_coupon_id, f"Promo code applied! {promo_code.get_discount_description()}"
            
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Error applying promo code: {str(e)}")
            return False, None, "An error occurred while applying the promo code"
    
    def _sync_to_stripe(self, promo_code: PromoCode) -> str:
        """Sync promo code to Stripe as a coupon
        
        Args:
            promo_code: PromoCode instance
        
        Returns:
            Stripe coupon ID
        """
        self._ensure_initialized()
        
        if promo_code.stripe_coupon_id:
            return promo_code.stripe_coupon_id
        
        try:
            # Create Stripe coupon
            coupon_params = {
                'name': promo_code.description or promo_code.code,
                'metadata': {
                    'promo_code_id': str(promo_code.id),
                    'code': promo_code.code,
                }
            }
            
            # Set discount amount
            if promo_code.discount_type == 'percent':
                coupon_params['percent_off'] = float(promo_code.discount_value)
            else:
                # Fixed amount in cents
                coupon_params['amount_off'] = int(promo_code.discount_value * 100)
                coupon_params['currency'] = 'eur'
            
            # Set duration
            if promo_code.duration == 'once':
                coupon_params['duration'] = 'once'
            elif promo_code.duration == 'forever':
                coupon_params['duration'] = 'forever'
            elif promo_code.duration == 'repeating':
                coupon_params['duration'] = 'repeating'
                coupon_params['duration_in_months'] = promo_code.duration_in_months
            
            # Set max redemptions
            if promo_code.max_redemptions:
                coupon_params['max_redemptions'] = promo_code.max_redemptions
            
            # Set expiry
            if promo_code.valid_until:
                import time
                coupon_params['redeem_by'] = int(time.mktime(promo_code.valid_until.timetuple()))
            
            # Create coupon in Stripe
            coupon = stripe.Coupon.create(**coupon_params)
            
            # Create promotion code in Stripe
            promotion_code = stripe.PromotionCode.create(
                coupon=coupon.id,
                code=promo_code.code,
                active=promo_code.is_active,
            )
            
            # Update promo code with Stripe IDs
            promo_code.stripe_coupon_id = coupon.id
            promo_code.stripe_promotion_code_id = promotion_code.id
            db.session.commit()
            
            current_app.logger.info(f"Synced promo code {promo_code.code} to Stripe: {coupon.id}")
            
            return coupon.id
            
        except stripe.error.StripeError as e:
            current_app.logger.error(f"Stripe error syncing promo code: {str(e)}")
            raise
    
    def create_promo_code(self, code: str, discount_type: str, discount_value: float,
                         duration: str = 'once', duration_in_months: int = None,
                         description: str = None, max_redemptions: int = None,
                         valid_until = None, first_time_only: bool = False,
                         sync_to_stripe: bool = True) -> PromoCode:
        """Create a new promo code
        
        Args:
            code: Unique promo code string
            discount_type: 'percent' or 'fixed'
            discount_value: Discount value (percentage or fixed amount)
            duration: 'once', 'repeating', or 'forever'
            duration_in_months: Number of months for repeating discounts
            description: Human-readable description
            max_redemptions: Maximum number of times code can be used
            valid_until: Expiration datetime
            first_time_only: Only allow new customers to use
            sync_to_stripe: Immediately sync to Stripe
        
        Returns:
            Created PromoCode instance
        """
        promo_code = PromoCode(
            code=code.upper(),
            description=description,
            discount_type=discount_type,
            discount_value=discount_value,
            duration=duration,
            duration_in_months=duration_in_months,
            max_redemptions=max_redemptions,
            valid_until=valid_until,
            first_time_only=first_time_only,
            is_active=True
        )
        
        db.session.add(promo_code)
        db.session.commit()
        
        if sync_to_stripe:
            try:
                self._sync_to_stripe(promo_code)
            except Exception as e:
                current_app.logger.error(f"Failed to sync promo code to Stripe: {str(e)}")
                # Don't fail the creation, just log the error
        
        return promo_code
    
    def get_promo_code_by_code(self, code: str) -> Optional[PromoCode]:
        """Get promo code by code string"""
        return PromoCode.query.filter_by(code=code.upper()).first()
    
    def deactivate_promo_code(self, code: str) -> bool:
        """Deactivate a promo code"""
        promo_code = self.get_promo_code_by_code(code)
        
        if not promo_code:
            return False
        
        promo_code.is_active = False
        db.session.commit()
        
        # Also deactivate in Stripe if synced
        if promo_code.stripe_promotion_code_id:
            try:
                self._ensure_initialized()
                stripe.PromotionCode.modify(
                    promo_code.stripe_promotion_code_id,
                    active=False
                )
            except stripe.error.StripeError as e:
                current_app.logger.error(f"Error deactivating Stripe promotion code: {str(e)}")
        
        return True
    
    def get_redemptions(self, promo_code: PromoCode) -> list:
        """Get all redemptions for a promo code"""
        return PromoCodeRedemption.query.filter_by(promo_code_id=promo_code.id).all()
    
    def get_organization_promo_codes(self, organization: Organization) -> list:
        """Get all promo codes used by an organization"""
        redemptions = PromoCodeRedemption.query.filter_by(organization_id=organization.id).all()
        return [r.promo_code for r in redemptions]


# Global instance
promo_code_service = PromoCodeService()


"""Promo Code Routes"""

from flask import Blueprint, request, jsonify, render_template, redirect, url_for, flash
from flask_login import login_required, current_user
from app.utils.promo_code_service import promo_code_service
from app.utils.tenancy import get_current_organization
from app.models.promo_code import PromoCode
from app import db

promo_codes_bp = Blueprint('promo_codes', __name__, url_prefix='/promo-codes')


@promo_codes_bp.route('/validate', methods=['POST'])
def validate_promo_code():
    """Validate a promo code (public endpoint for signup flow)"""
    data = request.get_json() or {}
    code = data.get('code', '').strip()
    
    if not code:
        return jsonify({
            'valid': False,
            'message': 'Please enter a promo code'
        }), 400
    
    is_valid, promo_code, message = promo_code_service.validate_promo_code(code)
    
    if is_valid:
        return jsonify({
            'valid': True,
            'code': promo_code.code,
            'description': promo_code.get_discount_description(),
            'message': message
        })
    else:
        return jsonify({
            'valid': False,
            'message': message
        }), 400


@promo_codes_bp.route('/apply', methods=['POST'])
@login_required
def apply_promo_code():
    """Apply a promo code to the current organization"""
    organization = get_current_organization()
    
    if not organization:
        return jsonify({
            'success': False,
            'message': 'Organization not found'
        }), 404
    
    data = request.get_json() or {}
    code = data.get('code', '').strip()
    
    if not code:
        return jsonify({
            'success': False,
            'message': 'Please enter a promo code'
        }), 400
    
    success, stripe_coupon_id, message = promo_code_service.apply_promo_code(
        code=code,
        organization=organization,
        user_id=current_user.id
    )
    
    if success:
        return jsonify({
            'success': True,
            'stripe_coupon_id': stripe_coupon_id,
            'message': message
        })
    else:
        return jsonify({
            'success': False,
            'message': message
        }), 400


@promo_codes_bp.route('/admin', methods=['GET'])
@login_required
def admin_promo_codes():
    """Admin page for managing promo codes"""
    # Check if user is admin
    if not current_user.is_admin:
        flash('Access denied. Admin privileges required.', 'error')
        return redirect(url_for('main.dashboard'))
    
    promo_codes = PromoCode.query.order_by(PromoCode.created_at.desc()).all()
    
    return render_template('admin/promo_codes.html', promo_codes=promo_codes)


@promo_codes_bp.route('/admin/create', methods=['POST'])
@login_required
def admin_create_promo_code():
    """Create a new promo code (admin only)"""
    # Check if user is admin
    if not current_user.is_admin:
        return jsonify({'success': False, 'message': 'Access denied'}), 403
    
    data = request.get_json() or {}
    
    try:
        from datetime import datetime
        
        # Parse valid_until if provided
        valid_until = None
        if data.get('valid_until'):
            valid_until = datetime.fromisoformat(data['valid_until'])
        
        promo_code = promo_code_service.create_promo_code(
            code=data['code'],
            discount_type=data['discount_type'],
            discount_value=float(data['discount_value']),
            duration=data.get('duration', 'once'),
            duration_in_months=data.get('duration_in_months'),
            description=data.get('description'),
            max_redemptions=data.get('max_redemptions'),
            valid_until=valid_until,
            first_time_only=data.get('first_time_only', False),
            sync_to_stripe=True
        )
        
        return jsonify({
            'success': True,
            'message': 'Promo code created successfully',
            'promo_code': {
                'id': promo_code.id,
                'code': promo_code.code,
                'description': promo_code.get_discount_description()
            }
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': str(e)
        }), 400


@promo_codes_bp.route('/admin/<int:promo_code_id>/deactivate', methods=['POST'])
@login_required
def admin_deactivate_promo_code(promo_code_id):
    """Deactivate a promo code (admin only)"""
    # Check if user is admin
    if not current_user.is_admin:
        return jsonify({'success': False, 'message': 'Access denied'}), 403
    
    promo_code = PromoCode.query.get_or_404(promo_code_id)
    
    promo_code.is_active = False
    db.session.commit()
    
    # Deactivate in Stripe
    promo_code_service.deactivate_promo_code(promo_code.code)
    
    return jsonify({
        'success': True,
        'message': 'Promo code deactivated'
    })


@promo_codes_bp.route('/admin/<int:promo_code_id>/stats', methods=['GET'])
@login_required
def admin_promo_code_stats(promo_code_id):
    """Get statistics for a promo code (admin only)"""
    # Check if user is admin
    if not current_user.is_admin:
        return jsonify({'success': False, 'message': 'Access denied'}), 403
    
    promo_code = PromoCode.query.get_or_404(promo_code_id)
    redemptions = promo_code_service.get_redemptions(promo_code)
    
    return jsonify({
        'code': promo_code.code,
        'description': promo_code.description,
        'times_redeemed': promo_code.times_redeemed,
        'max_redemptions': promo_code.max_redemptions,
        'is_active': promo_code.is_active,
        'is_valid': promo_code.is_valid,
        'redemptions': [{
            'organization_id': r.organization_id,
            'redeemed_at': r.redeemed_at.isoformat(),
            'redeemed_by': r.redeemed_by
        } for r in redemptions]
    })


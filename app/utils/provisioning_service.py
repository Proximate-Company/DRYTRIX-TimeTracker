"""
Provisioning Service

Handles automated tenant provisioning after successful payment or trial signup.
This includes creating default resources, setting up admin accounts, and triggering
welcome communications.
"""

from datetime import datetime
from typing import Dict, Any, Optional
from flask import current_app, url_for
from app import db
from app.models.organization import Organization
from app.models.user import User
from app.models.membership import Membership
from app.models.project import Project
from app.utils.email_service import email_service


class ProvisioningService:
    """Service for automated tenant provisioning and onboarding."""
    
    def provision_organization(self, organization: Organization, 
                             admin_user: Optional[User] = None,
                             trigger: str = 'payment') -> Dict[str, Any]:
        """Provision a new organization with default resources.
        
        This is the main entry point for provisioning. It:
        1. Creates a default project
        2. Sets up admin account if needed
        3. Initializes onboarding checklist
        4. Sends welcome email
        
        Args:
            organization: Organization to provision
            admin_user: Optional admin user (if already exists)
            trigger: Provisioning trigger ('payment', 'trial', 'manual')
        
        Returns:
            Dictionary with provisioning results
        """
        current_app.logger.info(f"Starting provisioning for organization {organization.name} (trigger: {trigger})")
        
        results = {
            'organization_id': organization.id,
            'organization_name': organization.name,
            'trigger': trigger,
            'provisioned_at': datetime.utcnow(),
            'resources_created': [],
            'errors': []
        }
        
        try:
            # 1. Create default project
            project = self._create_default_project(organization)
            if project:
                results['resources_created'].append(f"Default project: {project.name}")
                current_app.logger.info(f"Created default project '{project.name}' for {organization.name}")
            
            # 2. Ensure admin membership exists
            if admin_user:
                membership = self._ensure_admin_membership(organization, admin_user)
                if membership:
                    results['admin_user_id'] = admin_user.id
                    results['resources_created'].append(f"Admin membership for {admin_user.username}")
            
            # 3. Initialize onboarding checklist
            checklist = self._initialize_onboarding_checklist(organization)
            if checklist:
                results['resources_created'].append("Onboarding checklist")
                results['onboarding_checklist_id'] = checklist.id
            
            # 4. Mark organization as provisioned
            organization.status = 'active'
            db.session.commit()
            
            # 5. Send welcome email
            if admin_user and admin_user.email:
                email_sent = self._send_welcome_email(organization, admin_user, trigger)
                if email_sent:
                    results['resources_created'].append("Welcome email sent")
                else:
                    results['errors'].append("Failed to send welcome email")
            
            results['success'] = True
            current_app.logger.info(f"Successfully provisioned organization {organization.name}")
            
        except Exception as e:
            current_app.logger.error(f"Error provisioning organization {organization.name}: {e}", exc_info=True)
            results['success'] = False
            results['errors'].append(str(e))
            # Rollback any partial changes
            db.session.rollback()
        
        return results
    
    def provision_trial_organization(self, organization: Organization, 
                                   admin_user: User) -> Dict[str, Any]:
        """Provision a trial organization immediately upon signup.
        
        Args:
            organization: New organization
            admin_user: User who created the organization
        
        Returns:
            Provisioning results
        """
        current_app.logger.info(f"Provisioning trial organization: {organization.name}")
        
        # Mark as trial
        trial_days = current_app.config.get('STRIPE_TRIAL_DAYS', 14)
        from datetime import timedelta
        organization.trial_ends_at = datetime.utcnow() + timedelta(days=trial_days)
        organization.stripe_subscription_status = 'trialing'
        organization.subscription_plan = 'team'  # Default trial plan
        db.session.commit()
        
        # Provision the organization
        return self.provision_organization(organization, admin_user, trigger='trial')
    
    def _create_default_project(self, organization: Organization) -> Optional[Project]:
        """Create a default project for the organization.
        
        Args:
            organization: Organization instance
        
        Returns:
            Created Project or None if it fails
        """
        try:
            # Check if organization already has projects
            if organization.projects.count() > 0:
                current_app.logger.info(f"Organization {organization.name} already has projects, skipping default project creation")
                return None
            
            # Create default project
            project = Project(
                name="Getting Started",
                description="Your first project - feel free to rename or create new projects!",
                organization_id=organization.id,
                status='active',
                hourly_rate=0.00,
                currency_code=organization.currency
            )
            
            db.session.add(project)
            db.session.commit()
            
            return project
            
        except Exception as e:
            current_app.logger.error(f"Failed to create default project: {e}")
            db.session.rollback()
            return None
    
    def _ensure_admin_membership(self, organization: Organization, 
                                 user: User) -> Optional[Membership]:
        """Ensure user has admin membership in organization.
        
        Args:
            organization: Organization instance
            user: User to make admin
        
        Returns:
            Membership instance or None
        """
        try:
            # Check if membership already exists
            membership = Membership.find_membership(user.id, organization.id)
            
            if membership:
                # Ensure they're an admin
                if membership.role != 'admin':
                    membership.role = 'admin'
                    membership.status = 'active'
                    db.session.commit()
                return membership
            else:
                # Create new admin membership
                membership = Membership(
                    user_id=user.id,
                    organization_id=organization.id,
                    role='admin',
                    status='active'
                )
                db.session.add(membership)
                db.session.commit()
                return membership
                
        except Exception as e:
            current_app.logger.error(f"Failed to ensure admin membership: {e}")
            db.session.rollback()
            return None
    
    def _initialize_onboarding_checklist(self, organization: Organization) -> Optional['OnboardingChecklist']:
        """Initialize onboarding checklist for organization.
        
        Args:
            organization: Organization instance
        
        Returns:
            OnboardingChecklist instance or None
        """
        try:
            from app.models.onboarding_checklist import OnboardingChecklist
            
            # Check if checklist already exists
            existing = OnboardingChecklist.query.filter_by(
                organization_id=organization.id
            ).first()
            
            if existing:
                return existing
            
            # Create new checklist with default tasks
            checklist = OnboardingChecklist(
                organization_id=organization.id,
                created_at=datetime.utcnow()
            )
            
            db.session.add(checklist)
            db.session.commit()
            
            return checklist
            
        except Exception as e:
            current_app.logger.error(f"Failed to create onboarding checklist: {e}")
            db.session.rollback()
            return None
    
    def _send_welcome_email(self, organization: Organization, 
                           user: User, trigger: str) -> bool:
        """Send welcome email to new organization admin.
        
        Args:
            organization: Organization instance
            user: Admin user
            trigger: Provisioning trigger
        
        Returns:
            True if email sent successfully
        """
        try:
            # Build email content
            subject = f"Welcome to TimeTracker - {organization.name}"
            
            # Determine if trial or paid
            is_trial = organization.is_on_trial
            
            # Generate body
            body_text = self._generate_welcome_text(organization, user, is_trial)
            body_html = self._generate_welcome_html(organization, user, is_trial)
            
            # Send email
            return email_service.send_email(
                to_email=user.email,
                subject=subject,
                body_text=body_text,
                body_html=body_html
            )
            
        except Exception as e:
            current_app.logger.error(f"Failed to send welcome email: {e}")
            return False
    
    def _generate_welcome_text(self, organization: Organization, 
                              user: User, is_trial: bool) -> str:
        """Generate plain text welcome email."""
        
        trial_text = ""
        if is_trial:
            trial_text = f"""
You're on a {organization.trial_days_remaining}-day free trial. Explore all features with no credit card required!
Your trial ends on {organization.trial_ends_at.strftime('%B %d, %Y')}.
"""
        
        return f"""
Hello {user.display_name},

Welcome to TimeTracker! Your organization "{organization.name}" is now ready.
{trial_text}

🚀 GETTING STARTED

We've set up your account with:
- ✅ Your organization: {organization.name}
- ✅ A default project to get started
- ✅ Admin access for full control

📋 NEXT STEPS

1. Invite your team members
2. Create your first project (or customize the default one)
3. Set your working hours and preferences
4. Start tracking time!

Visit your dashboard: {url_for('main.dashboard', _external=True)}
Complete your onboarding: {url_for('onboarding.checklist', _external=True)}

💡 TIPS

- Use the command palette (Ctrl+K or ?) for quick navigation
- Set up billing information to avoid interruption after trial
- Explore our keyboard shortcuts for power users

Need help? Check out our documentation or contact support.

Best regards,
The TimeTracker Team
"""
    
    def _generate_welcome_html(self, organization: Organization, 
                               user: User, is_trial: bool) -> str:
        """Generate HTML welcome email."""
        
        trial_section = ""
        if is_trial:
            trial_section = f"""
            <div style="background-color: #fff3cd; padding: 15px; border-radius: 4px; margin: 20px 0; border-left: 4px solid #ffc107;">
                <p style="margin: 0; color: #856404;">
                    <strong>🎉 Free Trial Active</strong><br>
                    You have <strong>{organization.trial_days_remaining} days</strong> left in your trial. 
                    Explore all features with no credit card required!<br>
                    Trial ends: {organization.trial_ends_at.strftime('%B %d, %Y')}
                </p>
            </div>
            """
        
        return f"""
<!DOCTYPE html>
<html>
<head>
    <style>
        body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Arial, sans-serif; line-height: 1.6; color: #333; }}
        .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
        .header {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 30px; text-align: center; border-radius: 8px 8px 0 0; }}
        .header h1 {{ margin: 0; font-size: 28px; }}
        .content {{ background: white; padding: 30px; border: 1px solid #e0e0e0; border-top: none; }}
        .button {{ display: inline-block; padding: 14px 28px; background-color: #667eea; color: white; text-decoration: none; border-radius: 6px; margin: 20px 0; font-weight: 600; }}
        .button:hover {{ background-color: #5568d3; }}
        .checklist {{ background-color: #f8f9fa; padding: 20px; border-radius: 6px; margin: 20px 0; }}
        .checklist-item {{ padding: 10px 0; border-bottom: 1px solid #e0e0e0; }}
        .checklist-item:last-child {{ border-bottom: none; }}
        .tips {{ background-color: #e3f2fd; padding: 15px; border-radius: 4px; margin: 20px 0; border-left: 4px solid #2196f3; }}
        .footer {{ margin-top: 30px; padding-top: 20px; border-top: 1px solid #ddd; font-size: 12px; color: #666; text-align: center; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🎉 Welcome to TimeTracker!</h1>
            <p style="margin: 10px 0 0 0; font-size: 16px;">Your organization is ready</p>
        </div>
        
        <div class="content">
            <p>Hello {user.display_name},</p>
            
            <p>Congratulations! Your organization <strong>"{organization.name}"</strong> has been successfully set up and is ready to use.</p>
            
            {trial_section}
            
            <div class="checklist">
                <h3 style="margin-top: 0;">✨ We've set up your account with:</h3>
                <div class="checklist-item">✅ Your organization: <strong>{organization.name}</strong></div>
                <div class="checklist-item">✅ A default project to get started</div>
                <div class="checklist-item">✅ Admin access for full control</div>
            </div>
            
            <h3>📋 Next Steps</h3>
            <ol>
                <li><strong>Invite team members</strong> - Add your colleagues to collaborate</li>
                <li><strong>Create projects</strong> - Organize your work effectively</li>
                <li><strong>Set preferences</strong> - Configure working hours and settings</li>
                <li><strong>Start tracking</strong> - Begin logging your time</li>
            </ol>
            
            <div style="text-align: center;">
                <a href="{url_for('main.dashboard', _external=True)}" class="button">Go to Dashboard</a>
                <br>
                <a href="{url_for('onboarding.checklist', _external=True)}" style="color: #667eea; text-decoration: none; font-size: 14px;">
                    Complete your onboarding checklist →
                </a>
            </div>
            
            <div class="tips">
                <h4 style="margin-top: 0;">💡 Pro Tips</h4>
                <ul style="margin-bottom: 0;">
                    <li>Press <code>Ctrl+K</code> or <code>?</code> for quick navigation</li>
                    <li>Use keyboard shortcuts to work faster</li>
                    <li>Set up billing early to avoid trial expiration</li>
                </ul>
            </div>
            
            <p>If you have any questions, our support team is here to help!</p>
            
            <div class="footer">
                <p>Best regards,<br><strong>The TimeTracker Team</strong></p>
                <p style="color: #999; font-size: 11px;">
                    You received this email because you signed up for TimeTracker.
                </p>
            </div>
        </div>
    </div>
</body>
</html>
        """


# Create singleton instance
provisioning_service = ProvisioningService()


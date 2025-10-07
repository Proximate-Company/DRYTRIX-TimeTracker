from datetime import datetime
from app import db

class Membership(db.Model):
    """Membership model for user-organization relationships.
    
    This model represents the many-to-many relationship between users and
    organizations, with additional metadata like role and status. A user can
    belong to multiple organizations with different roles in each.
    """
    
    __tablename__ = 'memberships'
    __table_args__ = (
        # Ensure a user can only have one active membership per organization
        db.UniqueConstraint('user_id', 'organization_id', 'status', name='uq_user_org_status'),
        db.Index('idx_memberships_user_org', 'user_id', 'organization_id'),
        db.Index('idx_memberships_org_role', 'organization_id', 'role'),
    )
    
    id = db.Column(db.Integer, primary_key=True)
    
    # Foreign keys
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    organization_id = db.Column(db.Integer, db.ForeignKey('organizations.id'), nullable=False, index=True)
    
    # Role within the organization
    role = db.Column(db.String(20), default='member', nullable=False)  # 'admin', 'member', 'viewer'
    
    # Status
    status = db.Column(db.String(20), default='active', nullable=False)  # 'active', 'invited', 'suspended', 'removed'
    
    # Invitation details (for pending invitations)
    invited_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    invited_at = db.Column(db.DateTime, nullable=True)
    invitation_token = db.Column(db.String(100), unique=True, nullable=True, index=True)
    invitation_accepted_at = db.Column(db.DateTime, nullable=True)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Last activity tracking
    last_activity_at = db.Column(db.DateTime, nullable=True)
    
    # Relationships
    user = db.relationship('User', foreign_keys=[user_id], backref='memberships')
    organization = db.relationship('Organization', back_populates='memberships')
    inviter = db.relationship('User', foreign_keys=[invited_by], backref='sent_invitations')
    
    def __init__(self, user_id, organization_id, role='member', status='active', invited_by=None):
        """Create a new membership.
        
        Args:
            user_id: ID of the user
            organization_id: ID of the organization
            role: User's role in the organization ('admin', 'member', 'viewer')
            status: Membership status ('active', 'invited', 'suspended', 'removed')
            invited_by: ID of the user who sent the invitation (if applicable)
        """
        self.user_id = user_id
        self.organization_id = organization_id
        self.role = role
        self.status = status
        self.invited_by = invited_by
        
        if status == 'invited':
            self.invited_at = datetime.utcnow()
            self.invitation_token = self._generate_invitation_token()
    
    def __repr__(self):
        return f'<Membership user_id={self.user_id} org_id={self.organization_id} role={self.role}>'
    
    @property
    def is_active(self):
        """Check if membership is active"""
        return self.status == 'active'
    
    @property
    def is_admin(self):
        """Check if membership has admin role"""
        return self.role == 'admin'
    
    @property
    def is_pending(self):
        """Check if membership is pending (invited but not accepted)"""
        return self.status == 'invited'
    
    @property
    def can_manage_members(self):
        """Check if this member can manage other members"""
        return self.is_admin and self.is_active
    
    @property
    def can_manage_projects(self):
        """Check if this member can manage projects"""
        return self.role in ['admin', 'member'] and self.is_active
    
    @property
    def can_edit_data(self):
        """Check if this member can edit data"""
        return self.role in ['admin', 'member'] and self.is_active
    
    @property
    def is_readonly(self):
        """Check if this member has read-only access"""
        return self.role == 'viewer'
    
    def update_last_activity(self):
        """Update the last activity timestamp"""
        self.last_activity_at = datetime.utcnow()
        db.session.commit()
    
    def promote_to_admin(self):
        """Promote member to admin role"""
        if not self.is_active:
            raise ValueError("Cannot promote inactive member")
        
        self.role = 'admin'
        self.updated_at = datetime.utcnow()
        db.session.commit()
    
    def demote_from_admin(self):
        """Demote admin to regular member"""
        if not self.is_active:
            raise ValueError("Cannot demote inactive member")
        
        self.role = 'member'
        self.updated_at = datetime.utcnow()
        db.session.commit()
    
    def change_role(self, new_role):
        """Change member's role"""
        valid_roles = ['admin', 'member', 'viewer']
        if new_role not in valid_roles:
            raise ValueError(f"Invalid role. Must be one of: {', '.join(valid_roles)}")
        
        if not self.is_active:
            raise ValueError("Cannot change role of inactive member")
        
        self.role = new_role
        self.updated_at = datetime.utcnow()
        db.session.commit()
    
    def suspend(self):
        """Suspend the membership"""
        self.status = 'suspended'
        self.updated_at = datetime.utcnow()
        db.session.commit()
    
    def reactivate(self):
        """Reactivate a suspended membership"""
        if self.status != 'suspended':
            raise ValueError("Can only reactivate suspended memberships")
        
        self.status = 'active'
        self.updated_at = datetime.utcnow()
        db.session.commit()
    
    def remove(self):
        """Remove the membership (user leaves organization)"""
        self.status = 'removed'
        self.updated_at = datetime.utcnow()
        db.session.commit()
    
    def accept_invitation(self):
        """Accept a pending invitation"""
        if self.status != 'invited':
            raise ValueError("Can only accept invitations with 'invited' status")
        
        self.status = 'active'
        self.invitation_accepted_at = datetime.utcnow()
        self.invitation_token = None  # Clear the token after acceptance
        self.updated_at = datetime.utcnow()
        db.session.commit()
    
    def _generate_invitation_token(self):
        """Generate a unique invitation token"""
        import secrets
        return secrets.token_urlsafe(32)
    
    def to_dict(self, include_user=False, include_organization=False):
        """Convert membership to dictionary for API responses"""
        data = {
            'id': self.id,
            'user_id': self.user_id,
            'organization_id': self.organization_id,
            'role': self.role,
            'status': self.status,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'last_activity_at': self.last_activity_at.isoformat() if self.last_activity_at else None,
            'is_active': self.is_active,
            'is_admin': self.is_admin,
            'is_pending': self.is_pending,
            'can_manage_members': self.can_manage_members,
            'can_manage_projects': self.can_manage_projects,
            'can_edit_data': self.can_edit_data,
        }
        
        if self.is_pending:
            data.update({
                'invited_at': self.invited_at.isoformat() if self.invited_at else None,
                'invited_by': self.invited_by,
            })
        
        if include_user and self.user:
            data['user'] = {
                'id': self.user.id,
                'username': self.user.username,
                'email': self.user.email,
                'full_name': self.user.full_name,
                'display_name': self.user.display_name,
            }
        
        if include_organization and self.organization:
            data['organization'] = self.organization.to_dict()
        
        return data
    
    @classmethod
    def get_user_organizations(cls, user_id, status='active'):
        """Get all organizations a user belongs to"""
        query = cls.query.filter_by(user_id=user_id)
        
        if status:
            query = query.filter_by(status=status)
        
        return query.all()
    
    @classmethod
    def get_user_active_memberships(cls, user_id):
        """Get all active memberships for a user"""
        return cls.get_user_organizations(user_id, status='active')
    
    @classmethod
    def get_organization_members(cls, organization_id, role=None, status='active'):
        """Get all members of an organization"""
        query = cls.query.filter_by(organization_id=organization_id)
        
        if status:
            query = query.filter_by(status=status)
        
        if role:
            query = query.filter_by(role=role)
        
        return query.all()
    
    @classmethod
    def find_membership(cls, user_id, organization_id):
        """Find a membership for a user in an organization"""
        return cls.query.filter_by(
            user_id=user_id,
            organization_id=organization_id
        ).filter(cls.status.in_(['active', 'invited'])).first()
    
    @classmethod
    def user_is_member(cls, user_id, organization_id):
        """Check if user is an active member of an organization"""
        return cls.query.filter_by(
            user_id=user_id,
            organization_id=organization_id,
            status='active'
        ).first() is not None
    
    @classmethod
    def user_is_admin(cls, user_id, organization_id):
        """Check if user is an admin of an organization"""
        membership = cls.query.filter_by(
            user_id=user_id,
            organization_id=organization_id,
            status='active',
            role='admin'
        ).first()
        return membership is not None
    
    @classmethod
    def get_by_invitation_token(cls, token):
        """Get membership by invitation token"""
        return cls.query.filter_by(
            invitation_token=token,
            status='invited'
        ).first()


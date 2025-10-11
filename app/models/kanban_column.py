from app import db
from app.utils.timezone import now_in_app_timezone

class KanbanColumn(db.Model):
    """Model for custom Kanban board columns/task statuses"""
    
    __tablename__ = 'kanban_columns'
    
    id = db.Column(db.Integer, primary_key=True)
    key = db.Column(db.String(50), unique=True, nullable=False, index=True)  # Internal identifier (e.g. 'in_progress')
    label = db.Column(db.String(100), nullable=False)  # Display name (e.g. 'In Progress')
    icon = db.Column(db.String(100), default='fas fa-circle')  # Font Awesome icon class
    color = db.Column(db.String(50), default='secondary')  # Bootstrap color class or hex
    position = db.Column(db.Integer, nullable=False, default=0, index=True)  # Order in kanban board
    is_active = db.Column(db.Boolean, default=True, nullable=False)  # Can be disabled without deletion
    is_system = db.Column(db.Boolean, default=False, nullable=False)  # System columns cannot be deleted
    is_complete_state = db.Column(db.Boolean, default=False, nullable=False)  # Marks task as completed
    created_at = db.Column(db.DateTime, default=now_in_app_timezone, nullable=False)
    updated_at = db.Column(db.DateTime, default=now_in_app_timezone, onupdate=now_in_app_timezone, nullable=False)
    
    def __init__(self, **kwargs):
        """Initialize a new KanbanColumn"""
        super(KanbanColumn, self).__init__(**kwargs)
    
    def __repr__(self):
        return f'<KanbanColumn {self.key}: {self.label}>'
    
    def to_dict(self):
        """Convert column to dictionary for API responses"""
        return {
            'id': self.id,
            'key': self.key,
            'label': self.label,
            'icon': self.icon,
            'color': self.color,
            'position': self.position,
            'is_active': self.is_active,
            'is_system': self.is_system,
            'is_complete_state': self.is_complete_state,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
    
    @classmethod
    def get_active_columns(cls):
        """Get all active columns ordered by position"""
        try:
            # Force a fresh query by using db.session directly and avoiding cache
            from app import db
            # This ensures we always get fresh data from the database
            return db.session.query(cls).filter_by(is_active=True).order_by(cls.position.asc()).all()
        except Exception as e:
            # Table might not exist yet during migration
            print(f"Warning: Could not load kanban columns: {e}")
            return []
    
    @classmethod
    def get_all_columns(cls):
        """Get all columns (including inactive) ordered by position"""
        try:
            # Force a fresh query by using db.session directly and avoiding cache
            from app import db
            return db.session.query(cls).order_by(cls.position.asc()).all()
        except Exception as e:
            # Table might not exist yet during migration
            print(f"Warning: Could not load all kanban columns: {e}")
            return []
    
    @classmethod
    def get_column_by_key(cls, key):
        """Get column by its key"""
        try:
            return cls.query.filter_by(key=key).first()
        except Exception as e:
            # Table might not exist yet
            print(f"Warning: Could not find kanban column by key: {e}")
            return None
    
    @classmethod
    def get_valid_status_keys(cls):
        """Get list of all valid status keys (for validation)"""
        columns = cls.get_active_columns()
        if not columns:
            # Fallback to default statuses if table doesn't exist
            return ['todo', 'in_progress', 'review', 'done', 'cancelled']
        return [col.key for col in columns]
    
    @classmethod
    def initialize_default_columns(cls):
        """Initialize default kanban columns if none exist"""
        if cls.query.count() > 0:
            return False  # Columns already exist
        
        default_columns = [
            {
                'key': 'todo',
                'label': 'To Do',
                'icon': 'fas fa-list-check',
                'color': 'secondary',
                'position': 0,
                'is_system': True,
                'is_complete_state': False
            },
            {
                'key': 'in_progress',
                'label': 'In Progress',
                'icon': 'fas fa-spinner',
                'color': 'warning',
                'position': 1,
                'is_system': True,
                'is_complete_state': False
            },
            {
                'key': 'review',
                'label': 'Review',
                'icon': 'fas fa-user-check',
                'color': 'info',
                'position': 2,
                'is_system': False,
                'is_complete_state': False
            },
            {
                'key': 'done',
                'label': 'Done',
                'icon': 'fas fa-check-circle',
                'color': 'success',
                'position': 3,
                'is_system': True,
                'is_complete_state': True
            }
        ]
        
        for col_data in default_columns:
            column = cls(**col_data)
            db.session.add(column)
        
        db.session.commit()
        return True
    
    @classmethod
    def reorder_columns(cls, column_ids):
        """
        Reorder columns based on list of IDs
        column_ids: list of column IDs in the desired order
        """
        for position, col_id in enumerate(column_ids):
            column = cls.query.get(col_id)
            if column:
                column.position = position
                column.updated_at = now_in_app_timezone()
        
        db.session.commit()
        # Expire all cached data to force fresh reads
        db.session.expire_all()
        return True


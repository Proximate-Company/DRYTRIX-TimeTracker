"""
Onboarding Checklist Model

Tracks onboarding progress for organizations to help them get started
with the platform successfully.
"""

from datetime import datetime
from app import db
from typing import Dict, List


class OnboardingChecklist(db.Model):
    """Tracks onboarding progress for an organization.
    
    This model stores completion status of various onboarding tasks to help
    new organizations get up and running quickly.
    """
    
    __tablename__ = 'onboarding_checklists'
    
    id = db.Column(db.Integer, primary_key=True)
    organization_id = db.Column(db.Integer, db.ForeignKey('organizations.id'), 
                               nullable=False, unique=True, index=True)
    
    # Task completion flags
    invited_team_member = db.Column(db.Boolean, default=False, nullable=False)
    invited_team_member_at = db.Column(db.DateTime, nullable=True)
    
    created_project = db.Column(db.Boolean, default=False, nullable=False)
    created_project_at = db.Column(db.DateTime, nullable=True)
    
    created_time_entry = db.Column(db.Boolean, default=False, nullable=False)
    created_time_entry_at = db.Column(db.DateTime, nullable=True)
    
    set_working_hours = db.Column(db.Boolean, default=False, nullable=False)
    set_working_hours_at = db.Column(db.DateTime, nullable=True)
    
    customized_settings = db.Column(db.Boolean, default=False, nullable=False)
    customized_settings_at = db.Column(db.DateTime, nullable=True)
    
    added_billing_info = db.Column(db.Boolean, default=False, nullable=False)
    added_billing_info_at = db.Column(db.DateTime, nullable=True)
    
    created_client = db.Column(db.Boolean, default=False, nullable=False)
    created_client_at = db.Column(db.DateTime, nullable=True)
    
    generated_report = db.Column(db.Boolean, default=False, nullable=False)
    generated_report_at = db.Column(db.DateTime, nullable=True)
    
    # Overall status
    completed = db.Column(db.Boolean, default=False, nullable=False)
    completed_at = db.Column(db.DateTime, nullable=True)
    
    # Dismiss/skip tracking
    dismissed = db.Column(db.Boolean, default=False, nullable=False)
    dismissed_at = db.Column(db.DateTime, nullable=True)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, 
                          onupdate=datetime.utcnow, nullable=False)
    
    # Relationships
    organization = db.relationship('Organization', backref='onboarding_checklist')
    
    # Task definitions with metadata
    TASKS = {
        'invited_team_member': {
            'title': 'Invite your first team member',
            'description': 'Add colleagues to collaborate on projects',
            'icon': 'fa-user-plus',
            'priority': 1,
            'category': 'team'
        },
        'created_project': {
            'title': 'Create a project',
            'description': 'Organize your work with projects',
            'icon': 'fa-folder-plus',
            'priority': 2,
            'category': 'setup'
        },
        'created_time_entry': {
            'title': 'Log your first time entry',
            'description': 'Start tracking time on a project',
            'icon': 'fa-clock',
            'priority': 3,
            'category': 'usage'
        },
        'set_working_hours': {
            'title': 'Set your working hours',
            'description': 'Configure your schedule preferences',
            'icon': 'fa-calendar-alt',
            'priority': 4,
            'category': 'setup'
        },
        'created_client': {
            'title': 'Add your first client',
            'description': 'Manage client relationships and billing',
            'icon': 'fa-building',
            'priority': 5,
            'category': 'setup'
        },
        'customized_settings': {
            'title': 'Customize your settings',
            'description': 'Personalize TimeTracker to your needs',
            'icon': 'fa-cog',
            'priority': 6,
            'category': 'setup'
        },
        'added_billing_info': {
            'title': 'Add billing information',
            'description': 'Set up payment to continue after trial',
            'icon': 'fa-credit-card',
            'priority': 7,
            'category': 'billing'
        },
        'generated_report': {
            'title': 'Generate a report',
            'description': 'Analyze your time and productivity',
            'icon': 'fa-chart-bar',
            'priority': 8,
            'category': 'usage'
        },
    }
    
    def __repr__(self):
        return f'<OnboardingChecklist org_id={self.organization_id} completed={self.completed}>'
    
    @property
    def completion_percentage(self) -> int:
        """Calculate completion percentage."""
        if self.dismissed or self.completed:
            return 100
        
        total_tasks = len(self.TASKS)
        completed_tasks = self.get_completed_count()
        
        return int((completed_tasks / total_tasks) * 100)
    
    @property
    def is_complete(self) -> bool:
        """Check if all tasks are completed."""
        return self.completion_percentage == 100
    
    def get_completed_count(self) -> int:
        """Get number of completed tasks."""
        completed = 0
        for task_key in self.TASKS.keys():
            if getattr(self, task_key, False):
                completed += 1
        return completed
    
    def get_total_count(self) -> int:
        """Get total number of tasks."""
        return len(self.TASKS)
    
    def mark_task_complete(self, task_key: str) -> bool:
        """Mark a task as complete.
        
        Args:
            task_key: Key of the task (e.g., 'invited_team_member')
        
        Returns:
            True if task was marked complete, False if invalid task
        """
        if task_key not in self.TASKS:
            return False
        
        # Set completion flag and timestamp
        setattr(self, task_key, True)
        setattr(self, f"{task_key}_at", datetime.utcnow())
        
        self.updated_at = datetime.utcnow()
        
        # Check if all tasks are complete
        if self.get_completed_count() == self.get_total_count():
            self.completed = True
            self.completed_at = datetime.utcnow()
        
        db.session.commit()
        return True
    
    def dismiss(self) -> None:
        """Dismiss the onboarding checklist."""
        self.dismissed = True
        self.dismissed_at = datetime.utcnow()
        self.updated_at = datetime.utcnow()
        db.session.commit()
    
    def undismiss(self) -> None:
        """Re-enable the onboarding checklist."""
        self.dismissed = False
        self.dismissed_at = None
        self.updated_at = datetime.utcnow()
        db.session.commit()
    
    def get_tasks_with_status(self) -> List[Dict]:
        """Get all tasks with their completion status.
        
        Returns:
            List of task dictionaries with status information
        """
        tasks = []
        
        for task_key, task_meta in self.TASKS.items():
            is_complete = getattr(self, task_key, False)
            completed_at = getattr(self, f"{task_key}_at", None)
            
            task = {
                'key': task_key,
                'title': task_meta['title'],
                'description': task_meta['description'],
                'icon': task_meta['icon'],
                'priority': task_meta['priority'],
                'category': task_meta['category'],
                'completed': is_complete,
                'completed_at': completed_at.isoformat() if completed_at else None,
            }
            tasks.append(task)
        
        # Sort by priority
        tasks.sort(key=lambda x: x['priority'])
        
        return tasks
    
    def get_next_task(self) -> Dict:
        """Get the next incomplete task.
        
        Returns:
            Task dictionary or None if all complete
        """
        for task in self.get_tasks_with_status():
            if not task['completed']:
                return task
        return None
    
    def to_dict(self, include_tasks: bool = True) -> Dict:
        """Convert to dictionary for API responses.
        
        Args:
            include_tasks: Whether to include detailed task list
        
        Returns:
            Dictionary representation
        """
        data = {
            'id': self.id,
            'organization_id': self.organization_id,
            'completed': self.completed,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None,
            'dismissed': self.dismissed,
            'dismissed_at': self.dismissed_at.isoformat() if self.dismissed_at else None,
            'completion_percentage': self.completion_percentage,
            'completed_count': self.get_completed_count(),
            'total_count': self.get_total_count(),
            'is_complete': self.is_complete,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
        }
        
        if include_tasks:
            data['tasks'] = self.get_tasks_with_status()
            data['next_task'] = self.get_next_task()
        
        return data
    
    @classmethod
    def get_or_create(cls, organization_id: int) -> 'OnboardingChecklist':
        """Get existing checklist or create new one.
        
        Args:
            organization_id: Organization ID
        
        Returns:
            OnboardingChecklist instance
        """
        checklist = cls.query.filter_by(organization_id=organization_id).first()
        
        if not checklist:
            checklist = cls(organization_id=organization_id)
            db.session.add(checklist)
            db.session.commit()
        
        return checklist


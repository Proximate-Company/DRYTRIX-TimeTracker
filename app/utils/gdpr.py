"""
GDPR Compliance Utilities

This module provides data export and deletion functionality for GDPR compliance.
"""

import json
import csv
import io
from datetime import datetime, timedelta
from flask import current_app
from app import db
from app.models import User, TimeEntry, Project, Task, Invoice, InvoiceItem, Client, Comment, Organization


class GDPRExporter:
    """Handle GDPR data export requests"""
    
    @staticmethod
    def export_organization_data(organization_id, format='json'):
        """
        Export all data for an organization in GDPR-compliant format.
        
        Args:
            organization_id: The organization ID to export data for
            format: Export format ('json' or 'csv')
            
        Returns:
            dict or str: Exported data
        """
        from app.models import Membership
        
        organization = Organization.query.get(organization_id)
        if not organization:
            raise ValueError("Organization not found")
        
        # Collect all organization data
        data = {
            'export_date': datetime.utcnow().isoformat(),
            'organization': {
                'id': organization.id,
                'name': organization.name,
                'slug': organization.slug,
                'contact_email': organization.contact_email,
                'created_at': organization.created_at.isoformat() if organization.created_at else None,
                'status': organization.status,
            },
            'members': [],
            'projects': [],
            'clients': [],
            'time_entries': [],
            'tasks': [],
            'invoices': [],
        }
        
        # Export members
        memberships = Membership.query.filter_by(organization_id=organization_id).all()
        for membership in memberships:
            user = membership.user
            data['members'].append({
                'username': user.username,
                'email': user.email,
                'full_name': user.full_name,
                'role': membership.role,
                'joined_at': membership.created_at.isoformat() if membership.created_at else None,
            })
        
        # Export clients
        clients = Client.query.filter_by(organization_id=organization_id).all()
        for client in clients:
            data['clients'].append({
                'name': client.name,
                'email': client.email,
                'phone': client.phone,
                'address': client.address,
                'contact_person': client.contact_person,
                'created_at': client.created_at.isoformat() if client.created_at else None,
            })
        
        # Export projects
        projects = Project.query.filter_by(organization_id=organization_id).all()
        for project in projects:
            data['projects'].append({
                'name': project.name,
                'description': project.description,
                'client': project.client_obj.name if project.client_obj else None,
                'billable': project.billable,
                'hourly_rate': float(project.hourly_rate) if project.hourly_rate else None,
                'status': project.status,
                'created_at': project.created_at.isoformat() if project.created_at else None,
            })
        
        # Export time entries
        time_entries = TimeEntry.query.filter_by(organization_id=organization_id).all()
        for entry in time_entries:
            data['time_entries'].append({
                'user': entry.user.username if entry.user else None,
                'project': entry.project.name if entry.project else None,
                'start_time': entry.start_time.isoformat() if entry.start_time else None,
                'end_time': entry.end_time.isoformat() if entry.end_time else None,
                'duration_seconds': entry.duration_seconds,
                'notes': entry.notes,
                'tags': entry.tags,
                'billable': entry.billable,
            })
        
        # Export tasks
        tasks = Task.query.filter_by(organization_id=organization_id).all()
        for task in tasks:
            data['tasks'].append({
                'name': task.name,
                'description': task.description,
                'project': task.project.name if task.project else None,
                'status': task.status,
                'priority': task.priority,
                'assigned_to': task.assigned_user.username if task.assigned_user else None,
                'created_by': task.creator.username if task.creator else None,
                'due_date': task.due_date.isoformat() if task.due_date else None,
                'created_at': task.created_at.isoformat() if task.created_at else None,
            })
        
        # Export invoices
        invoices = Invoice.query.filter_by(organization_id=organization_id).all()
        for invoice in invoices:
            invoice_data = {
                'invoice_number': invoice.invoice_number,
                'client_name': invoice.client_name,
                'client_email': invoice.client_email,
                'issue_date': invoice.issue_date.isoformat() if invoice.issue_date else None,
                'due_date': invoice.due_date.isoformat() if invoice.due_date else None,
                'status': invoice.status,
                'subtotal': float(invoice.subtotal) if invoice.subtotal else None,
                'tax_rate': float(invoice.tax_rate) if invoice.tax_rate else None,
                'total_amount': float(invoice.total_amount) if invoice.total_amount else None,
                'items': [],
            }
            
            # Add invoice items
            for item in invoice.items:
                invoice_data['items'].append({
                    'description': item.description,
                    'quantity': float(item.quantity) if item.quantity else None,
                    'unit_price': float(item.unit_price) if item.unit_price else None,
                    'total_amount': float(item.total_amount) if item.total_amount else None,
                })
            
            data['invoices'].append(invoice_data)
        
        if format == 'csv':
            return GDPRExporter._convert_to_csv(data)
        
        return data
    
    @staticmethod
    def export_user_data(user_id, format='json'):
        """
        Export all data for a specific user.
        
        Args:
            user_id: The user ID to export data for
            format: Export format ('json' or 'csv')
            
        Returns:
            dict or str: Exported data
        """
        user = User.query.get(user_id)
        if not user:
            raise ValueError("User not found")
        
        data = {
            'export_date': datetime.utcnow().isoformat(),
            'user': {
                'username': user.username,
                'email': user.email,
                'full_name': user.full_name,
                'created_at': user.created_at.isoformat() if user.created_at else None,
                'last_login': user.last_login.isoformat() if user.last_login else None,
                'role': user.role,
                'totp_enabled': user.totp_enabled,
            },
            'time_entries': [],
            'tasks_created': [],
            'tasks_assigned': [],
            'comments': [],
        }
        
        # Export time entries
        time_entries = TimeEntry.query.filter_by(user_id=user_id).all()
        for entry in time_entries:
            data['time_entries'].append({
                'project': entry.project.name if entry.project else None,
                'start_time': entry.start_time.isoformat() if entry.start_time else None,
                'end_time': entry.end_time.isoformat() if entry.end_time else None,
                'duration_seconds': entry.duration_seconds,
                'notes': entry.notes,
                'tags': entry.tags,
            })
        
        # Export created tasks
        created_tasks = Task.query.filter_by(created_by=user_id).all()
        for task in created_tasks:
            data['tasks_created'].append({
                'name': task.name,
                'description': task.description,
                'project': task.project.name if task.project else None,
                'status': task.status,
                'created_at': task.created_at.isoformat() if task.created_at else None,
            })
        
        # Export assigned tasks
        assigned_tasks = Task.query.filter_by(assigned_to=user_id).all()
        for task in assigned_tasks:
            data['tasks_assigned'].append({
                'name': task.name,
                'description': task.description,
                'project': task.project.name if task.project else None,
                'status': task.status,
                'due_date': task.due_date.isoformat() if task.due_date else None,
            })
        
        # Export comments
        try:
            comments = Comment.query.filter_by(user_id=user_id).all()
            for comment in comments:
                data['comments'].append({
                    'content': comment.content,
                    'created_at': comment.created_at.isoformat() if comment.created_at else None,
                })
        except Exception:
            # Comment model might not exist
            pass
        
        if format == 'csv':
            return GDPRExporter._convert_to_csv(data)
        
        return data
    
    @staticmethod
    def _convert_to_csv(data):
        """Convert JSON data to CSV format"""
        # For simplicity, create a CSV with flattened data
        # In production, you might want to create multiple CSV files
        output = io.StringIO()
        
        # Write metadata
        output.write(f"Export Date,{data['export_date']}\n\n")
        
        # Write each section
        for section, items in data.items():
            if section == 'export_date':
                continue
            
            if isinstance(items, list) and items:
                output.write(f"\n{section.upper()}\n")
                
                # Get headers from first item
                if isinstance(items[0], dict):
                    headers = list(items[0].keys())
                    writer = csv.DictWriter(output, fieldnames=headers)
                    writer.writeheader()
                    writer.writerows(items)
                
                output.write('\n')
        
        return output.getvalue()


class GDPRDeleter:
    """Handle GDPR data deletion requests"""
    
    @staticmethod
    def request_organization_deletion(organization_id, requested_by_user_id):
        """
        Request deletion of an organization and all its data.
        Implements grace period before actual deletion.
        
        Args:
            organization_id: The organization ID to delete
            requested_by_user_id: User who requested the deletion
            
        Returns:
            dict: Deletion request details
        """
        organization = Organization.query.get(organization_id)
        if not organization:
            raise ValueError("Organization not found")
        
        # Check if user is an admin of the organization
        if not organization.is_admin(requested_by_user_id):
            raise PermissionError("Only organization admins can request deletion")
        
        # Calculate deletion date (grace period)
        grace_days = current_app.config.get('GDPR_DELETION_DELAY_DAYS', 30)
        deletion_date = datetime.utcnow() + timedelta(days=grace_days)
        
        # Mark organization for deletion
        organization.deleted_at = deletion_date
        organization.status = 'pending_deletion'
        
        db.session.commit()
        
        return {
            'organization_id': organization_id,
            'deletion_scheduled_for': deletion_date.isoformat(),
            'grace_period_days': grace_days,
            'can_cancel_until': deletion_date.isoformat(),
        }
    
    @staticmethod
    def cancel_organization_deletion(organization_id, user_id):
        """
        Cancel a pending organization deletion.
        
        Args:
            organization_id: The organization ID
            user_id: User requesting cancellation
            
        Returns:
            bool: Success status
        """
        organization = Organization.query.get(organization_id)
        if not organization:
            raise ValueError("Organization not found")
        
        # Check if user is an admin
        if not organization.is_admin(user_id):
            raise PermissionError("Only organization admins can cancel deletion")
        
        # Check if deletion is pending
        if organization.status != 'pending_deletion':
            raise ValueError("No pending deletion to cancel")
        
        # Cancel deletion
        organization.deleted_at = None
        organization.status = 'active'
        
        db.session.commit()
        
        return True
    
    @staticmethod
    def execute_organization_deletion(organization_id):
        """
        Permanently delete an organization and all its data.
        This should only be called after the grace period has expired.
        
        Args:
            organization_id: The organization ID to delete
            
        Returns:
            dict: Deletion summary
        """
        organization = Organization.query.get(organization_id)
        if not organization:
            raise ValueError("Organization not found")
        
        # Verify grace period has expired
        if organization.deleted_at and datetime.utcnow() < organization.deleted_at:
            raise ValueError("Grace period has not expired yet")
        
        # Collect statistics before deletion
        stats = {
            'organization_id': organization_id,
            'organization_name': organization.name,
            'members_deleted': organization.member_count,
            'projects_deleted': organization.project_count,
            'deletion_date': datetime.utcnow().isoformat(),
        }
        
        # Delete all related data (CASCADE will handle most of this)
        # But we'll be explicit for clarity
        
        # Delete time entries
        TimeEntry.query.filter_by(organization_id=organization_id).delete()
        
        # Delete tasks
        Task.query.filter_by(organization_id=organization_id).delete()
        
        # Delete invoice items (via invoices cascade)
        Invoice.query.filter_by(organization_id=organization_id).delete()
        
        # Delete projects
        Project.query.filter_by(organization_id=organization_id).delete()
        
        # Delete clients
        Client.query.filter_by(organization_id=organization_id).delete()
        
        # Delete memberships
        from app.models import Membership
        Membership.query.filter_by(organization_id=organization_id).delete()
        
        # Finally, delete the organization
        db.session.delete(organization)
        db.session.commit()
        
        return stats
    
    @staticmethod
    def delete_user_data(user_id):
        """
        Delete a user and anonymize their data.
        
        Args:
            user_id: The user ID to delete
            
        Returns:
            dict: Deletion summary
        """
        user = User.query.get(user_id)
        if not user:
            raise ValueError("User not found")
        
        stats = {
            'user_id': user_id,
            'username': user.username,
            'deletion_date': datetime.utcnow().isoformat(),
        }
        
        # Anonymize time entries instead of deleting
        # (needed for billing/audit purposes)
        time_entries = TimeEntry.query.filter_by(user_id=user_id).all()
        for entry in time_entries:
            entry.notes = "[User data deleted]"
        
        # Reassign or delete tasks
        created_tasks = Task.query.filter_by(created_by=user_id).all()
        for task in created_tasks:
            task.created_by = None
        
        assigned_tasks = Task.query.filter_by(assigned_to=user_id).all()
        for task in assigned_tasks:
            task.assigned_to = None
        
        # Delete user memberships
        from app.models import Membership
        Membership.query.filter_by(user_id=user_id).delete()
        
        # Finally, delete the user
        db.session.delete(user)
        db.session.commit()
        
        return stats
    
    @staticmethod
    def cleanup_expired_data():
        """
        Clean up data that has exceeded retention period.
        Should be run as a scheduled task.
        
        Returns:
            dict: Cleanup summary
        """
        retention_days = current_app.config.get('DATA_RETENTION_DAYS', 0)
        
        if retention_days == 0:
            return {'message': 'Data retention not configured'}
        
        cutoff_date = datetime.utcnow() - timedelta(days=retention_days)
        
        # Delete old time entries
        old_entries = TimeEntry.query.filter(
            TimeEntry.created_at < cutoff_date
        ).delete()
        
        # Execute pending organization deletions
        pending_deletions = Organization.query.filter(
            Organization.status == 'pending_deletion',
            Organization.deleted_at <= datetime.utcnow()
        ).all()
        
        deleted_orgs = 0
        for org in pending_deletions:
            try:
                GDPRDeleter.execute_organization_deletion(org.id)
                deleted_orgs += 1
            except Exception as e:
                current_app.logger.error(f"Failed to delete organization {org.id}: {e}")
        
        db.session.commit()
        
        return {
            'old_entries_deleted': old_entries,
            'organizations_deleted': deleted_orgs,
            'cutoff_date': cutoff_date.isoformat(),
        }


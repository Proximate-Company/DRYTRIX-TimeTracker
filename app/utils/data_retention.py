"""
Data Retention Policy Enforcement

This module provides utilities for enforcing data retention policies
and cleaning up old data according to configured rules.
"""

from datetime import datetime, timedelta
from flask import current_app
from app import db
from app.models import TimeEntry, Task, Invoice, Organization
from app.utils.gdpr import GDPRDeleter


class DataRetentionPolicy:
    """Enforce data retention policies"""
    
    @staticmethod
    def cleanup_old_data():
        """
        Clean up data that has exceeded retention period.
        This should be run as a scheduled task (e.g., daily cron job).
        
        Returns:
            dict: Summary of cleanup operations
        """
        retention_days = current_app.config.get('DATA_RETENTION_DAYS', 0)
        
        summary = {
            'retention_days': retention_days,
            'cleanup_date': datetime.utcnow().isoformat(),
            'items_cleaned': {
                'time_entries': 0,
                'completed_tasks': 0,
                'old_invoices': 0,
                'pending_deletions': 0,
            },
            'errors': []
        }
        
        if retention_days == 0:
            current_app.logger.info("Data retention not configured, skipping cleanup")
            return summary
        
        cutoff_date = datetime.utcnow() - timedelta(days=retention_days)
        current_app.logger.info(f"Starting data retention cleanup. Cutoff date: {cutoff_date}")
        
        try:
            # Clean up old completed time entries
            # Only delete entries that are completed and not associated with unpaid invoices
            old_entries = TimeEntry.query.filter(
                TimeEntry.created_at < cutoff_date,
                TimeEntry.end_time.isnot(None)
            ).all()
            
            entries_to_delete = []
            for entry in old_entries:
                # Check if entry is part of an unpaid invoice
                if not DataRetentionPolicy._is_entry_in_unpaid_invoice(entry):
                    entries_to_delete.append(entry)
            
            for entry in entries_to_delete:
                db.session.delete(entry)
            
            summary['items_cleaned']['time_entries'] = len(entries_to_delete)
            
        except Exception as e:
            current_app.logger.error(f"Error cleaning up time entries: {e}")
            summary['errors'].append(f"Time entries cleanup failed: {str(e)}")
        
        try:
            # Clean up old completed tasks
            old_tasks = Task.query.filter(
                Task.created_at < cutoff_date,
                Task.status.in_(['completed', 'cancelled'])
            ).all()
            
            for task in old_tasks:
                db.session.delete(task)
            
            summary['items_cleaned']['completed_tasks'] = len(old_tasks)
            
        except Exception as e:
            current_app.logger.error(f"Error cleaning up tasks: {e}")
            summary['errors'].append(f"Tasks cleanup failed: {str(e)}")
        
        try:
            # Clean up very old draft invoices
            # Keep paid/sent invoices for longer (e.g., 7 years for tax purposes)
            draft_cutoff = datetime.utcnow() - timedelta(days=90)  # Delete drafts older than 90 days
            
            old_drafts = Invoice.query.filter(
                Invoice.created_at < draft_cutoff,
                Invoice.status == 'draft'
            ).all()
            
            for invoice in old_drafts:
                db.session.delete(invoice)
            
            summary['items_cleaned']['old_invoices'] = len(old_drafts)
            
        except Exception as e:
            current_app.logger.error(f"Error cleaning up invoices: {e}")
            summary['errors'].append(f"Invoices cleanup failed: {str(e)}")
        
        try:
            # Process pending organization deletions
            pending_deletions = Organization.query.filter(
                Organization.status == 'pending_deletion',
                Organization.deleted_at <= datetime.utcnow()
            ).all()
            
            deleted_count = 0
            for org in pending_deletions:
                try:
                    GDPRDeleter.execute_organization_deletion(org.id)
                    deleted_count += 1
                except Exception as e:
                    current_app.logger.error(f"Failed to delete organization {org.id}: {e}")
                    summary['errors'].append(f"Organization {org.id} deletion failed: {str(e)}")
            
            summary['items_cleaned']['pending_deletions'] = deleted_count
            
        except Exception as e:
            current_app.logger.error(f"Error processing pending deletions: {e}")
            summary['errors'].append(f"Pending deletions processing failed: {str(e)}")
        
        # Commit all changes
        try:
            db.session.commit()
            current_app.logger.info(f"Data retention cleanup completed: {summary}")
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Failed to commit cleanup changes: {e}")
            summary['errors'].append(f"Commit failed: {str(e)}")
        
        return summary
    
    @staticmethod
    def _is_entry_in_unpaid_invoice(time_entry):
        """
        Check if a time entry is part of an unpaid invoice.
        
        Args:
            time_entry: TimeEntry object
            
        Returns:
            bool: True if entry is in an unpaid invoice
        """
        from app.models import InvoiceItem
        
        # Find invoice items that reference this time entry
        invoice_items = InvoiceItem.query.filter(
            InvoiceItem.time_entry_ids.contains(str(time_entry.id))
        ).all()
        
        for item in invoice_items:
            if item.invoice and item.invoice.status in ['sent', 'overdue']:
                return True
        
        return False
    
    @staticmethod
    def get_retention_summary():
        """
        Get a summary of data subject to retention policies.
        
        Returns:
            dict: Summary of retainable data
        """
        retention_days = current_app.config.get('DATA_RETENTION_DAYS', 0)
        
        if retention_days == 0:
            return {
                'enabled': False,
                'message': 'Data retention policies are not configured'
            }
        
        cutoff_date = datetime.utcnow() - timedelta(days=retention_days)
        
        # Count items subject to cleanup
        old_entries_count = TimeEntry.query.filter(
            TimeEntry.created_at < cutoff_date,
            TimeEntry.end_time.isnot(None)
        ).count()
        
        old_tasks_count = Task.query.filter(
            Task.created_at < cutoff_date,
            Task.status.in_(['completed', 'cancelled'])
        ).count()
        
        draft_cutoff = datetime.utcnow() - timedelta(days=90)
        old_drafts_count = Invoice.query.filter(
            Invoice.created_at < draft_cutoff,
            Invoice.status == 'draft'
        ).count()
        
        pending_deletions_count = Organization.query.filter(
            Organization.status == 'pending_deletion',
            Organization.deleted_at <= datetime.utcnow()
        ).count()
        
        return {
            'enabled': True,
            'retention_days': retention_days,
            'cutoff_date': cutoff_date.isoformat(),
            'items_eligible_for_cleanup': {
                'time_entries': old_entries_count,
                'completed_tasks': old_tasks_count,
                'draft_invoices': old_drafts_count,
                'pending_organization_deletions': pending_deletions_count,
            },
            'next_cleanup': 'Manual trigger required or configure scheduled task'
        }
    
    @staticmethod
    def export_before_deletion(organization_id):
        """
        Export organization data before deletion for archival purposes.
        
        Args:
            organization_id: Organization ID to export
            
        Returns:
            dict: Export summary
        """
        from app.utils.gdpr import GDPRExporter
        import json
        import os
        
        try:
            # Create exports directory if it doesn't exist
            exports_dir = os.path.join(current_app.root_path, '..', 'data', 'exports')
            os.makedirs(exports_dir, exist_ok=True)
            
            # Export data
            data = GDPRExporter.export_organization_data(organization_id, format='json')
            
            # Save to file
            filename = f"org_{organization_id}_export_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.json"
            filepath = os.path.join(exports_dir, filename)
            
            with open(filepath, 'w') as f:
                json.dump(data, f, indent=2)
            
            current_app.logger.info(f"Exported organization {organization_id} data to {filepath}")
            
            return {
                'success': True,
                'filename': filename,
                'filepath': filepath,
                'export_date': datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            current_app.logger.error(f"Failed to export organization {organization_id}: {e}")
            return {
                'success': False,
                'error': str(e)
            }


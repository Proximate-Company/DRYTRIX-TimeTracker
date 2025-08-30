from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, send_file
from flask_login import login_required, current_user
from app import db
from app.models import User, Project, TimeEntry, Invoice, InvoiceItem, Settings
from datetime import datetime, timedelta, date
from decimal import Decimal
import io
import csv
import json

invoices_bp = Blueprint('invoices', __name__)

@invoices_bp.route('/invoices')
@login_required
def list_invoices():
    """List all invoices"""
    # Get invoices (scope by user unless admin)
    if current_user.is_admin:
        invoices = Invoice.query.order_by(Invoice.created_at.desc()).all()
    else:
        invoices = Invoice.query.filter_by(created_by=current_user.id).order_by(Invoice.created_at.desc()).all()
    
    # Get summary statistics
    total_invoices = len(invoices)
    total_amount = sum(invoice.total_amount for invoice in invoices)
    paid_amount = sum(invoice.total_amount for invoice in invoices if invoice.status == 'paid')
    overdue_amount = sum(invoice.total_amount for invoice in invoices if invoice.status == 'overdue')
    
    summary = {
        'total_invoices': total_invoices,
        'total_amount': float(total_amount),
        'paid_amount': float(paid_amount),
        'overdue_amount': float(overdue_amount),
        'outstanding_amount': float(total_amount - paid_amount)
    }
    
    return render_template('invoices/list.html', invoices=invoices, summary=summary)

@invoices_bp.route('/invoices/create', methods=['GET', 'POST'])
@login_required
def create_invoice():
    """Create a new invoice"""
    if request.method == 'POST':
        # Get form data
        project_id = request.form.get('project_id', type=int)
        client_name = request.form.get('client_name', '').strip()
        client_email = request.form.get('client_email', '').strip()
        client_address = request.form.get('client_address', '').strip()
        due_date_str = request.form.get('due_date', '').strip()
        tax_rate = request.form.get('tax_rate', '0').strip()
        notes = request.form.get('notes', '').strip()
        terms = request.form.get('terms', '').strip()
        
        # Validate required fields
        if not project_id or not client_name or not due_date_str:
            flash('Project, client name, and due date are required', 'error')
            return render_template('invoices/create.html')
        
        try:
            due_date = datetime.strptime(due_date_str, '%Y-%m-%d').date()
        except ValueError:
            flash('Invalid due date format', 'error')
            return render_template('invoices/create.html')
        
        try:
            tax_rate = Decimal(tax_rate)
        except ValueError:
            flash('Invalid tax rate format', 'error')
            return render_template('invoices/create.html')
        
        # Get project
        project = Project.query.get(project_id)
        if not project:
            flash('Selected project not found', 'error')
            return render_template('invoices/create.html')
        
        # Generate invoice number
        invoice_number = Invoice.generate_invoice_number()
        
        # Create invoice
        invoice = Invoice(
            invoice_number=invoice_number,
            project_id=project_id,
            client_name=client_name,
            due_date=due_date,
            created_by=current_user.id,
            client_email=client_email,
            client_address=client_address,
            tax_rate=tax_rate,
            notes=notes,
            terms=terms
        )
        
        db.session.add(invoice)
        db.session.commit()
        
        flash(f'Invoice {invoice_number} created successfully', 'success')
        return redirect(url_for('invoices.edit_invoice', invoice_id=invoice.id))
    
    # GET request - show form
    projects = Project.query.filter_by(status='active', billable=True).order_by(Project.name).all()
    settings = Settings.get_settings()
    
    # Set default due date to 30 days from now
    default_due_date = (datetime.utcnow() + timedelta(days=30)).strftime('%Y-%m-%d')
    
    return render_template('invoices/create.html', 
                         projects=projects, 
                         settings=settings,
                         default_due_date=default_due_date)

@invoices_bp.route('/invoices/<int:invoice_id>')
@login_required
def view_invoice(invoice_id):
    """View invoice details"""
    invoice = Invoice.query.get_or_404(invoice_id)
    
    # Check access permissions
    if not current_user.is_admin and invoice.created_by != current_user.id:
        flash('You do not have permission to view this invoice', 'error')
        return redirect(url_for('invoices.list_invoices'))
    
    return render_template('invoices/view.html', invoice=invoice)

@invoices_bp.route('/invoices/<int:invoice_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_invoice(invoice_id):
    """Edit invoice"""
    invoice = Invoice.query.get_or_404(invoice_id)
    
    # Check access permissions
    if not current_user.is_admin and invoice.created_by != current_user.id:
        flash('You do not have permission to edit this invoice', 'error')
        return redirect(url_for('invoices.list_invoices'))
    
    if request.method == 'POST':
        # Update invoice details
        invoice.client_name = request.form.get('client_name', '').strip()
        invoice.client_email = request.form.get('client_email', '').strip()
        invoice.client_address = request.form.get('client_address', '').strip()
        invoice.due_date = datetime.strptime(request.form.get('due_date'), '%Y-%m-%d').date()
        invoice.tax_rate = Decimal(request.form.get('tax_rate', '0'))
        invoice.notes = request.form.get('notes', '').strip()
        invoice.terms = request.form.get('terms', '').strip()
        
        # Update items
        item_ids = request.form.getlist('item_id[]')
        descriptions = request.form.getlist('description[]')
        quantities = request.form.getlist('quantity[]')
        unit_prices = request.form.getlist('unit_price[]')
        
        # Remove existing items
        invoice.items.delete()
        
        # Add new items
        for i in range(len(descriptions)):
            if descriptions[i].strip() and quantities[i] and unit_prices[i]:
                try:
                    quantity = Decimal(quantities[i])
                    unit_price = Decimal(unit_prices[i])
                    
                    item = InvoiceItem(
                        invoice_id=invoice.id,
                        description=descriptions[i].strip(),
                        quantity=quantity,
                        unit_price=unit_price
                    )
                    db.session.add(item)
                except ValueError:
                    flash(f'Invalid quantity or price for item {i+1}', 'error')
                    continue
        
        # Calculate totals
        invoice.calculate_totals()
        db.session.commit()
        
        flash('Invoice updated successfully', 'success')
        return redirect(url_for('invoices.view_invoice', invoice_id=invoice.id))
    
    # GET request - show edit form
    projects = Project.query.filter_by(status='active').order_by(Project.name).all()
    return render_template('invoices/edit.html', invoice=invoice, projects=projects)

@invoices_bp.route('/invoices/<int:invoice_id>/status', methods=['POST'])
@login_required
def update_invoice_status(invoice_id):
    """Update invoice status"""
    invoice = Invoice.query.get_or_404(invoice_id)
    
    # Check access permissions
    if not current_user.is_admin and invoice.created_by != current_user.id:
        return jsonify({'error': 'Permission denied'}), 403
    
    new_status = request.form.get('new_status')
    if new_status not in ['draft', 'sent', 'paid', 'cancelled']:
        return jsonify({'error': 'Invalid status'}), 400
    
    invoice.status = new_status
    db.session.commit()
    
    return jsonify({'success': True, 'status': new_status})

@invoices_bp.route('/invoices/<int:invoice_id>/delete', methods=['POST'])
@login_required
def delete_invoice(invoice_id):
    """Delete invoice"""
    invoice = Invoice.query.get_or_404(invoice_id)
    
    # Check access permissions
    if not current_user.is_admin and invoice.created_by != current_user.id:
        flash('You do not have permission to delete this invoice', 'error')
        return redirect(url_for('invoices.list_invoices'))
    
    invoice_number = invoice.invoice_number
    db.session.delete(invoice)
    db.session.commit()
    
    flash(f'Invoice {invoice_number} deleted successfully', 'success')
    return redirect(url_for('invoices.list_invoices'))

@invoices_bp.route('/invoices/<int:invoice_id>/generate-from-time', methods=['GET', 'POST'])
@login_required
def generate_from_time(invoice_id):
    """Generate invoice items from time entries"""
    invoice = Invoice.query.get_or_404(invoice_id)
    
    # Check access permissions
    if not current_user.is_admin and invoice.created_by != current_user.id:
        flash('You do not have permission to edit this invoice', 'error')
        return redirect(url_for('invoices.list_invoices'))
    
    if request.method == 'POST':
        # Get selected time entries
        selected_entries = request.form.getlist('time_entries[]')
        if not selected_entries:
            flash('No time entries selected', 'error')
            return redirect(url_for('invoices.generate_from_time', invoice_id=invoice.id))
        
        # Clear existing items
        invoice.items.delete()
        
        # Group time entries by task/project and create invoice items
        time_entries = TimeEntry.query.filter(TimeEntry.id.in_(selected_entries)).all()
        
        # Group by task (if available) or project
        grouped_entries = {}
        for entry in time_entries:
            if entry.task_id:
                key = f"task_{entry.task_id}"
                if key not in grouped_entries:
                    grouped_entries[key] = {
                        'description': f"Task: {entry.task.name if entry.task else 'Unknown Task'}",
                        'entries': [],
                        'total_hours': 0
                    }
            else:
                key = f"project_{entry.project_id}"
                if key not in grouped_entries:
                    grouped_entries[key] = {
                        'description': f"Project: {entry.project.name}",
                        'entries': [],
                        'total_hours': 0
                    }
            
            grouped_entries[key]['entries'].append(entry)
            grouped_entries[key]['total_hours'] += entry.duration_hours
        
        # Create invoice items
        for group in grouped_entries.values():
            # Use project hourly rate or default
            hourly_rate = invoice.project.hourly_rate or Decimal('0')
            
            item = InvoiceItem(
                invoice_id=invoice.id,
                description=group['description'],
                quantity=group['total_hours'],
                unit_price=hourly_rate,
                time_entry_ids=','.join(str(entry.id) for entry in group['entries'])
            )
            db.session.add(item)
        
        # Calculate totals
        invoice.calculate_totals()
        db.session.commit()
        
        flash('Invoice items generated from time entries successfully', 'success')
        return redirect(url_for('invoices.edit_invoice', invoice_id=invoice.id))
    
    # GET request - show time entry selection
    # Get unbilled time entries for this project
    time_entries = TimeEntry.query.filter(
        TimeEntry.project_id == invoice.project_id,
        TimeEntry.end_time.isnot(None),
        TimeEntry.billable == True
    ).order_by(TimeEntry.start_time.desc()).all()
    
    # Filter out entries already billed in other invoices
    unbilled_entries = []
    for entry in time_entries:
        # Check if this entry is already billed in another invoice
        already_billed = False
        for other_invoice in invoice.project.invoices:
            if other_invoice.id != invoice.id:
                for item in other_invoice.items:
                    if item.time_entry_ids and str(entry.id) in item.time_entry_ids.split(','):
                        already_billed = True
                        break
                if already_billed:
                    break
        
        if not already_billed:
            unbilled_entries.append(entry)
    
    # Calculate total available hours
    total_available_hours = sum(entry.duration_hours for entry in unbilled_entries)
    
    # Get currency from settings
    settings = Settings.get_settings()
    currency = settings.currency if settings else 'USD'
    
    return render_template('invoices/generate_from_time.html', 
                         invoice=invoice, 
                         time_entries=unbilled_entries,
                         total_available_hours=total_available_hours,
                         currency=currency)

@invoices_bp.route('/invoices/<int:invoice_id>/export/csv')
@login_required
def export_invoice_csv(invoice_id):
    """Export invoice as CSV"""
    invoice = Invoice.query.get_or_404(invoice_id)
    
    # Check access permissions
    if not current_user.is_admin and invoice.created_by != current_user.id:
        flash('You do not have permission to export this invoice', 'error')
        return redirect(url_for('invoices.list_invoices'))
    
    # Create CSV output
    output = io.StringIO()
    writer = csv.writer(output)
    
    # Write header
    writer.writerow(['Invoice Number', invoice.invoice_number])
    writer.writerow(['Client', invoice.client_name])
    writer.writerow(['Issue Date', invoice.issue_date.strftime('%Y-%m-%d')])
    writer.writerow(['Due Date', invoice.due_date.strftime('%Y-%m-%d')])
    writer.writerow(['Status', invoice.status])
    writer.writerow([])
    
    # Write items
    writer.writerow(['Description', 'Quantity (Hours)', 'Unit Price', 'Total Amount'])
    for item in invoice.items:
        writer.writerow([
            item.description,
            float(item.quantity),
            float(item.unit_price),
            float(item.total_amount)
        ])
    
    writer.writerow([])
    writer.writerow(['Subtotal', '', '', float(invoice.subtotal)])
    writer.writerow(['Tax Rate', '', '', f'{float(invoice.tax_rate)}%'])
    writer.writerow(['Tax Amount', '', '', float(invoice.tax_amount)])
    writer.writerow(['Total Amount', '', '', float(invoice.total_amount)])
    
    output.seek(0)
    
    filename = f'invoice_{invoice.invoice_number}.csv'
    
    return send_file(
        io.BytesIO(output.getvalue().encode('utf-8')),
        mimetype='text/csv',
        as_attachment=True,
        download_name=filename
    )

@invoices_bp.route('/invoices/<int:invoice_id>/export/pdf')
@login_required
def export_invoice_pdf(invoice_id):
    """Export invoice as PDF"""
    invoice = Invoice.query.get_or_404(invoice_id)
    
    # Check access permissions
    if not current_user.is_admin and invoice.created_by != current_user.id:
        flash('You do not have permission to export this invoice', 'error')
        return redirect(url_for('invoices.list_invoices'))
    
    try:
        from app.utils.pdf_generator import InvoicePDFGenerator
        
        # Generate PDF
        pdf_generator = InvoicePDFGenerator(invoice)
        pdf_bytes = pdf_generator.generate_pdf()
        
        filename = f'invoice_{invoice.invoice_number}.pdf'
        
        return send_file(
            io.BytesIO(pdf_bytes),
            mimetype='application/pdf',
            as_attachment=True,
            download_name=filename
        )
        
    except ImportError:
        flash('PDF generation is not available. Please install WeasyPrint.', 'error')
        return redirect(url_for('invoices.view_invoice', invoice_id=invoice.id))
    except Exception as e:
        # Try fallback PDF generator
        try:
            from app.utils.pdf_generator_fallback import InvoicePDFGeneratorFallback
            
            flash('WeasyPrint failed, using fallback PDF generator. PDF quality may be reduced.', 'warning')
            
            # Generate PDF using fallback
            pdf_generator = InvoicePDFGeneratorFallback(invoice)
            pdf_bytes = pdf_generator.generate_pdf()
            
            filename = f'invoice_{invoice.invoice_number}.pdf'
            
            return send_file(
                io.BytesIO(pdf_bytes),
                mimetype='application/pdf',
                as_attachment=True,
                download_name=filename
            )
            
        except Exception as fallback_error:
            flash(f'PDF generation failed: {str(e)}. Fallback also failed: {str(fallback_error)}', 'error')
            return redirect(url_for('invoices.view_invoice', invoice_id=invoice.id))

@invoices_bp.route('/invoices/<int:invoice_id>/duplicate')
@login_required
def duplicate_invoice(invoice_id):
    """Duplicate an existing invoice"""
    original_invoice = Invoice.query.get_or_404(invoice_id)
    
    # Check access permissions
    if not current_user.is_admin and original_invoice.created_by != current_user.id:
        flash('You do not have permission to duplicate this invoice', 'error')
        return redirect(url_for('invoices.list_invoices'))
    
    # Generate new invoice number
    new_invoice_number = Invoice.generate_invoice_number()
    
    # Create new invoice
    new_invoice = Invoice(
        invoice_number=new_invoice_number,
        project_id=original_invoice.project_id,
        client_name=original_invoice.client_name,
        client_email=original_invoice.client_email,
        client_address=original_invoice.client_address,
        due_date=original_invoice.due_date + timedelta(days=30),  # 30 days from original due date
        created_by=current_user.id,
        tax_rate=original_invoice.tax_rate,
        notes=original_invoice.notes,
        terms=original_invoice.terms
    )
    
    db.session.add(new_invoice)
    db.session.commit()
    
    # Duplicate items
    for original_item in original_invoice.items:
        new_item = InvoiceItem(
            invoice_id=new_invoice.id,
            description=original_item.description,
            quantity=original_item.quantity,
            unit_price=original_item.unit_price
        )
        db.session.add(new_item)
    
    # Calculate totals
    new_invoice.calculate_totals()
    db.session.commit()
    
    flash(f'Invoice {new_invoice_number} created as duplicate', 'success')
    return redirect(url_for('invoices.edit_invoice', invoice_id=new_invoice.id))

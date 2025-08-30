"""
PDF Generation utility for invoices
Uses WeasyPrint to generate professional PDF invoices
"""

import os
from datetime import datetime
from weasyprint import HTML, CSS
from weasyprint.text.fonts import FontConfiguration
from app.models import Settings

class InvoicePDFGenerator:
    """Generate PDF invoices with company branding"""
    
    def __init__(self, invoice, settings=None):
        self.invoice = invoice
        self.settings = settings or Settings.get_settings()
    
    def generate_pdf(self):
        """Generate PDF content and return as bytes"""
        html_content = self._generate_html()
        css_content = self._generate_css()
        
        # Configure fonts
        font_config = FontConfiguration()
        
        # Create PDF
        html_doc = HTML(string=html_content)
        css_doc = CSS(string=css_content, font_config=font_config)
        
        pdf_bytes = html_doc.write_pdf(
            stylesheets=[css_doc],
            font_config=font_config
        )
        
        return pdf_bytes
    
    def _generate_html(self):
        """Generate HTML content for the invoice"""
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <title>Invoice {self.invoice.invoice_number}</title>
        </head>
        <body>
            <div class="invoice-container">
                <!-- Header -->
                <div class="header">
                    <div class="company-info">
                        {self._get_company_logo_html()}
                        <div class="company-details">
                            <h1 class="company-name">{self.settings.company_name}</h1>
                            <div class="company-address">{self.settings.company_address|nl2br}</div>
                            <div class="company-contact">
                                <span>Email: {self.settings.company_email}</span>
                                <span>Phone: {self.settings.company_phone}</span>
                                <span>Website: {self.settings.company_website}</span>
                            </div>
                            {self._get_company_tax_info()}
                        </div>
                    </div>
                    <div class="invoice-info">
                        <h2 class="invoice-title">INVOICE</h2>
                        <div class="invoice-details">
                            <div class="detail-row">
                                <span class="label">Invoice #:</span>
                                <span class="value">{self.invoice.invoice_number}</span>
                            </div>
                            <div class="detail-row">
                                <span class="label">Issue Date:</span>
                                <span class="value">{self.invoice.issue_date.strftime('%B %d, %Y')}</span>
                            </div>
                            <div class="detail-row">
                                <span class="label">Due Date:</span>
                                <span class="value">{self.invoice.due_date.strftime('%B %d, %Y')}</span>
                            </div>
                            <div class="detail-row">
                                <span class="label">Status:</span>
                                <span class="value status-{self.invoice.status}">{self.invoice.status.title()}</span>
                            </div>
                        </div>
                    </div>
                </div>
                
                <!-- Client Information -->
                <div class="client-section">
                    <h3>Bill To:</h3>
                    <div class="client-info">
                        <div class="client-name">{self.invoice.client_name}</div>
                        {self._get_client_email_html()}
                        {self._get_client_address_html()}
                    </div>
                </div>
                
                <!-- Project Information -->
                <div class="project-section">
                    <h3>Project:</h3>
                    <div class="project-info">
                        <strong>{self.invoice.project.name}</strong>
                        {self._get_project_description_html()}
                    </div>
                </div>
                
                <!-- Invoice Items -->
                <div class="items-section">
                    <table class="invoice-table">
                        <thead>
                            <tr>
                                <th class="description">Description</th>
                                <th class="quantity">Quantity (Hours)</th>
                                <th class="unit-price">Unit Price</th>
                                <th class="total">Total Amount</th>
                            </tr>
                        </thead>
                        <tbody>
                            {self._generate_items_rows()}
                        </tbody>
                        <tfoot>
                            {self._generate_totals_rows()}
                        </tfoot>
                    </table>
                </div>
                
                <!-- Additional Information -->
                {self._get_additional_info_html()}
                
                <!-- Footer -->
                <div class="footer">
                    <div class="payment-info">
                        {self._get_payment_info_html()}
                    </div>
                    <div class="terms">
                        <h4>Terms & Conditions:</h4>
                        <p>{self.settings.invoice_terms}</p>
                    </div>
                </div>
            </div>
        </body>
        </html>
        """
        return html
    
    def _get_company_logo_html(self):
        """Generate HTML for company logo if available"""
        if self.settings.has_logo():
            logo_path = self.settings.get_logo_path()
            if logo_path and os.path.exists(logo_path):
                return f'<img src="{logo_path}" alt="Company Logo" class="company-logo">'
        return ''
    
    def _get_company_tax_info(self):
        """Generate HTML for company tax information"""
        if self.settings.company_tax_id:
            return f'<div class="company-tax">Tax ID: {self.settings.company_tax_id}</div>'
        return ''
    
    def _get_client_email_html(self):
        """Generate HTML for client email if available"""
        if self.invoice.client_email:
            return f'<div class="client-email">{self.invoice.client_email}</div>'
        return ''
    
    def _get_client_address_html(self):
        """Generate HTML for client address if available"""
        if self.invoice.client_address:
            return f'<div class="client-address">{self.invoice.client_address}</div>'
        return ''
    
    def _get_project_description_html(self):
        """Generate HTML for project description if available"""
        if self.invoice.project.description:
            return f'<div class="project-description">{self.invoice.project.description}</div>'
        return ''
    
    def _generate_items_rows(self):
        """Generate HTML rows for invoice items"""
        rows = []
        for item in self.invoice.items:
            row = f"""
            <tr>
                <td class="description">
                    {item.description}
                    {self._get_time_entry_info_html(item)}
                </td>
                <td class="quantity text-center">{item.quantity:.2f}</td>
                <td class="unit-price text-right">{item.unit_price:.2f} {self.settings.currency}</td>
                <td class="total text-right">{item.total_amount:.2f} {self.settings.currency}</td>
            </tr>
            """
            rows.append(row)
        return ''.join(rows)
    
    def _get_time_entry_info_html(self, item):
        """Generate HTML for time entry information if available"""
        if item.time_entry_ids:
            count = len(item.time_entry_ids.split(','))
            return f'<br><small class="time-entry-info">Generated from {count} time entries</small>'
        return ''
    
    def _generate_totals_rows(self):
        """Generate HTML rows for invoice totals"""
        rows = []
        
        # Subtotal
        rows.append(f"""
        <tr class="subtotal">
            <td colspan="3" class="text-right"><strong>Subtotal:</strong></td>
            <td class="text-right"><strong>{self.invoice.subtotal:.2f} {self.settings.currency}</strong></td>
        </tr>
        """)
        
        # Tax if applicable
        if self.invoice.tax_rate > 0:
            rows.append(f"""
            <tr class="tax">
                <td colspan="3" class="text-right">
                    <strong>Tax ({self.invoice.tax_rate:.2f}%):</strong>
                </td>
                <td class="text-right"><strong>{self.invoice.tax_amount:.2f} {self.settings.currency}</strong></td>
            </tr>
            """)
        
        # Total
        rows.append(f"""
        <tr class="total">
            <td colspan="3" class="text-right"><strong>Total Amount:</strong></td>
            <td class="text-right"><strong>{self.invoice.total_amount:.2f} {self.settings.currency}</strong></td>
        </tr>
        """)
        
        return ''.join(rows)
    
    def _get_additional_info_html(self):
        """Generate HTML for additional invoice information"""
        html_parts = []
        
        if self.invoice.notes:
            html_parts.append(f"""
            <div class="notes-section">
                <h4>Notes:</h4>
                <p>{self.invoice.notes}</p>
            </div>
            """)
        
        if self.invoice.terms:
            html_parts.append(f"""
            <div class="terms-section">
                <h4>Terms:</h4>
                <p>{self.invoice.terms}</p>
            </div>
            """)
        
        if html_parts:
            return f'<div class="additional-info">{"".join(html_parts)}</div>'
        return ''
    
    def _get_payment_info_html(self):
        """Generate HTML for payment information"""
        if self.settings.company_bank_info:
            return f"""
            <h4>Payment Information:</h4>
            <div class="bank-info">{self.settings.company_bank_info}</div>
            """
        return ''
    
    def _generate_css(self):
        """Generate CSS styles for the invoice"""
        return """
        @page {
            size: A4;
            margin: 2cm;
            @bottom-center {
                content: "Page " counter(page) " of " counter(pages);
                font-size: 10pt;
                color: #666;
            }
        }
        
        body {
            font-family: 'Helvetica Neue', Arial, sans-serif;
            font-size: 12pt;
            line-height: 1.4;
            color: #333;
            margin: 0;
            padding: 0;
        }
        
        .invoice-container {
            max-width: 100%;
        }
        
        .header {
            display: flex;
            justify-content: space-between;
            align-items: flex-start;
            margin-bottom: 2em;
            border-bottom: 2px solid #007bff;
            padding-bottom: 1em;
        }
        
        .company-info {
            flex: 1;
        }
        
        .company-logo {
            max-width: 150px;
            max-height: 80px;
            display: block;
            margin-left: auto;
            margin-right: 0;
            margin-bottom: 1em;
        }
        
        .company-name {
            font-size: 24pt;
            font-weight: bold;
            color: #007bff;
            margin: 0 0 0.5em 0;
        }
        
        .company-address {
            margin-bottom: 0.5em;
            line-height: 1.3;
        }
        
        .company-contact {
            margin-bottom: 0.5em;
        }
        
        .company-contact span {
            display: block;
            margin-bottom: 0.2em;
            font-size: 10pt;
        }
        
        .company-tax {
            font-size: 10pt;
            color: #666;
        }
        
        .invoice-info {
            text-align: right;
            min-width: 200px;
        }
        
        .logo-container {
            text-align: right;
            margin-bottom: 1em;
        }
        
        .invoice-title {
            font-size: 28pt;
            font-weight: bold;
            color: #007bff;
            margin: 0 0 1em 0;
        }
        
        .invoice-details .detail-row {
            margin-bottom: 0.5em;
        }
        
        .detail-row .label {
            font-weight: bold;
            margin-right: 0.5em;
        }
        
        .status-draft { color: #6c757d; }
        .status-sent { color: #17a2b8; }
        .status-paid { color: #28a745; }
        .status-overdue { color: #dc3545; }
        .status-cancelled { color: #343a40; }
        
        .client-section, .project-section {
            margin-bottom: 2em;
        }
        
        .client-section h3, .project-section h3 {
            font-size: 14pt;
            font-weight: bold;
            color: #007bff;
            margin: 0 0 0.5em 0;
            border-bottom: 1px solid #dee2e6;
            padding-bottom: 0.3em;
        }
        
        .client-name {
            font-weight: bold;
            font-size: 14pt;
            margin-bottom: 0.5em;
        }
        
        .client-email, .client-address, .project-description {
            margin-bottom: 0.3em;
            color: #666;
        }
        
        .items-section {
            margin-bottom: 2em;
        }
        
        .invoice-table {
            width: 100%;
            border-collapse: collapse;
            margin-bottom: 1em;
        }
        
        .invoice-table th,
        .invoice-table td {
            border: 1px solid #dee2e6;
            padding: 0.75em;
            text-align: left;
        }
        
        .invoice-table th {
            background-color: #f8f9fa;
            font-weight: bold;
            color: #495057;
        }
        
        .description { width: 40%; }
        .quantity { width: 15%; text-align: center; }
        .unit-price { width: 20%; text-align: right; }
        .total { width: 25%; text-align: right; }
        
        .text-center { text-align: center; }
        .text-right { text-align: right; }
        
        .time-entry-info {
            color: #6c757d;
            font-style: italic;
        }
        
        .subtotal { background-color: #f8f9fa; }
        .tax { background-color: #fff3cd; }
        .total { background-color: #d1ecf1; font-weight: bold; }
        
        .additional-info {
            margin-bottom: 2em;
        }
        
        .notes-section, .terms-section {
            margin-bottom: 1em;
        }
        
        .notes-section h4, .terms-section h4 {
            font-size: 12pt;
            font-weight: bold;
            color: #495057;
            margin: 0 0 0.5em 0;
        }
        
        .footer {
            margin-top: 2em;
            padding-top: 1em;
            border-top: 1px solid #dee2e6;
        }
        
        .payment-info {
            margin-bottom: 1em;
        }
        
        .payment-info h4 {
            font-size: 12pt;
            font-weight: bold;
            color: #495057;
            margin: 0 0 0.5em 0;
        }
        
        .bank-info {
            color: #666;
            line-height: 1.3;
        }
        
        .terms h4 {
            font-size: 12pt;
            font-weight: bold;
            color: #495057;
            margin: 0 0 0.5em 0;
        }
        
        .terms p {
            color: #666;
            line-height: 1.3;
        }
        
        /* Utility classes */
        .nl2br {
            white-space: pre-line;
        }
        """

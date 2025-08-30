"""
Fallback PDF Generation utility for invoices using ReportLab
This is used when WeasyPrint is not available due to system dependencies
"""

import os
from datetime import datetime
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.enums import TA_LEFT, TA_RIGHT, TA_CENTER
from reportlab.pdfgen import canvas
from app.models import Settings

class InvoicePDFGeneratorFallback:
    """Generate PDF invoices with company branding using ReportLab"""
    
    def __init__(self, invoice, settings=None):
        self.invoice = invoice
        self.settings = settings or Settings.get_settings()
        self.styles = getSampleStyleSheet()
        self._setup_custom_styles()
    
    def _setup_custom_styles(self):
        """Setup custom paragraph styles"""
        self.styles.add(ParagraphStyle(
            name='CompanyName',
            parent=self.styles['Heading1'],
            fontSize=18,
            spaceAfter=12,
            textColor=colors.HexColor('#007bff')
        ))
        
        self.styles.add(ParagraphStyle(
            name='InvoiceTitle',
            parent=self.styles['Heading1'],
            fontSize=24,
            spaceAfter=20,
            textColor=colors.HexColor('#007bff'),
            alignment=TA_RIGHT
        ))
        
        self.styles.add(ParagraphStyle(
            name='SectionHeader',
            parent=self.styles['Heading2'],
            fontSize=14,
            spaceAfter=8,
            textColor=colors.HexColor('#007bff')
        ))
        
        self.styles.add(ParagraphStyle(
            name='NormalText',
            parent=self.styles['Normal'],
            fontSize=10,
            spaceAfter=6
        ))
    
    def generate_pdf(self):
        """Generate PDF content and return as bytes"""
        # Create a temporary file to store the PDF
        import tempfile
        import io
        
        with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as tmp_file:
            tmp_path = tmp_file.name
        
        try:
            # Generate the PDF
            doc = SimpleDocTemplate(
                tmp_path,
                pagesize=A4,
                rightMargin=2*cm,
                leftMargin=2*cm,
                topMargin=2*cm,
                bottomMargin=2*cm
            )
            
            # Build the story (content)
            story = self._build_story()
            
            # Build the PDF
            doc.build(story)
            
            # Read the generated PDF
            with open(tmp_path, 'rb') as f:
                pdf_bytes = f.read()
            
            return pdf_bytes
            
        finally:
            # Clean up temporary file
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)
    
    def _build_story(self):
        """Build the PDF content story"""
        story = []
        
        # Header section
        story.extend(self._build_header())
        story.append(Spacer(1, 20))
        
        # Client and project information
        story.extend(self._build_client_section())
        story.append(Spacer(1, 20))
        
        # Invoice items table
        story.extend(self._build_items_table())
        story.append(Spacer(1, 20))
        
        # Additional information
        story.extend(self._build_additional_info())
        story.append(Spacer(1, 20))
        
        # Footer
        story.extend(self._build_footer())
        
        return story
    
    def _build_header(self):
        """Build the header section with company info and invoice details"""
        story = []
        
        # Company information (left side)
        company_info = []
        company_info.append(Paragraph(self.settings.company_name, self.styles['CompanyName']))
        
        if self.settings.company_address:
            company_info.append(Paragraph(self.settings.company_address, self.styles['NormalText']))
        
        if self.settings.company_email:
            company_info.append(Paragraph(f"Email: {self.settings.company_email}", self.styles['NormalText']))
        
        if self.settings.company_phone:
            company_info.append(Paragraph(f"Phone: {self.settings.company_phone}", self.styles['NormalText']))
        
        if self.settings.company_website:
            company_info.append(Paragraph(f"Website: {self.settings.company_website}", self.styles['NormalText']))
        
        if self.settings.company_tax_id:
            company_info.append(Paragraph(f"Tax ID: {self.settings.company_tax_id}", self.styles['NormalText']))
        
        # Invoice information (right side)
        invoice_info = []
        
        # Add logo if available (top right)
        if self.settings.has_logo():
            logo_path = self.settings.get_logo_path()
            if logo_path and os.path.exists(logo_path):
                # Add a placeholder for the logo - in ReportLab we'd need to use canvas.drawImage
                # For now, we'll add a note that logo is included
                invoice_info.append(Paragraph("[Company Logo]", self.styles['NormalText']))
        
        invoice_info.append(Paragraph("INVOICE", self.styles['InvoiceTitle']))
        invoice_info.append(Paragraph(f"Invoice #: {self.invoice.invoice_number}", self.styles['NormalText']))
        invoice_info.append(Paragraph(f"Issue Date: {self.invoice.issue_date.strftime('%B %d, %Y')}", self.styles['NormalText']))
        invoice_info.append(Paragraph(f"Due Date: {self.invoice.due_date.strftime('%B %d, %Y')}", self.styles['NormalText']))
        invoice_info.append(Paragraph(f"Status: {self.invoice.status.title()}", self.styles['NormalText']))
        
        # Create a table to layout company info and invoice info side by side
        header_data = [[company_info, invoice_info]]
        header_table = Table(header_data, colWidths=[7*cm, 7*cm])
        header_table.setStyle(TableStyle([
            ('ALIGN', (0, 0), (0, 0), 'LEFT'),
            ('ALIGN', (1, 0), (1, 0), 'RIGHT'),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ]))
        
        story.append(header_table)
        return story
    
    def _build_client_section(self):
        """Build the client and project information section"""
        story = []
        
        # Client information
        story.append(Paragraph("Bill To:", self.styles['SectionHeader']))
        story.append(Paragraph(self.invoice.client_name, self.styles['NormalText']))
        
        if self.invoice.client_email:
            story.append(Paragraph(self.invoice.client_email, self.styles['NormalText']))
        
        if self.invoice.client_address:
            story.append(Paragraph(self.invoice.client_address, self.styles['NormalText']))
        
        story.append(Spacer(1, 12))
        
        # Project information
        story.append(Paragraph("Project:", self.styles['SectionHeader']))
        story.append(Paragraph(self.invoice.project.name, self.styles['NormalText']))
        
        if self.invoice.project.description:
            story.append(Paragraph(self.invoice.project.description, self.styles['NormalText']))
        
        return story
    
    def _build_items_table(self):
        """Build the invoice items table"""
        story = []
        
        story.append(Paragraph("Invoice Items", self.styles['SectionHeader']))
        
        # Table headers
        headers = ['Description', 'Quantity (Hours)', 'Unit Price', 'Total Amount']
        
        # Table data
        data = [headers]
        for item in self.invoice.items:
            row = [
                item.description,
                f"{item.quantity:.2f}",
                f"{item.unit_price:.2f} {self.settings.currency}",
                f"{item.total_amount:.2f} {self.settings.currency}"
            ]
            data.append(row)
        
        # Add totals
        data.append(['', '', 'Subtotal:', f"{self.invoice.subtotal:.2f} {self.settings.currency}"])
        
        if self.invoice.tax_rate > 0:
            data.append(['', '', f'Tax ({self.invoice.tax_rate:.2f}%):', f"{self.invoice.tax_amount:.2f} {self.settings.currency}"])
        
        data.append(['', '', 'Total Amount:', f"{self.invoice.total_amount:.2f} {self.settings.currency}"])
        
        # Create table
        table = Table(data, colWidths=[8*cm, 3*cm, 3*cm, 3*cm])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('ALIGN', (0, 1), (0, -1), 'LEFT'),  # Description column left-aligned
            ('ALIGN', (1, 1), (-1, -1), 'RIGHT'),  # Numbers right-aligned
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 12),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, -3), (-1, -1), colors.lightgrey),
            ('FONTNAME', (0, -3), (-1, -1), 'Helvetica-Bold'),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        
        story.append(table)
        return story
    
    def _build_additional_info(self):
        """Build additional information section"""
        story = []
        
        if self.invoice.notes:
            story.append(Paragraph("Notes:", self.styles['SectionHeader']))
            story.append(Paragraph(self.invoice.notes, self.styles['NormalText']))
            story.append(Spacer(1, 12))
        
        if self.invoice.terms:
            story.append(Paragraph("Terms:", self.styles['SectionHeader']))
            story.append(Paragraph(self.invoice.terms, self.styles['NormalText']))
            story.append(Spacer(1, 12))
        
        return story
    
    def _build_footer(self):
        """Build the footer section"""
        story = []
        
        # Payment information
        if self.settings.company_bank_info:
            story.append(Paragraph("Payment Information:", self.styles['SectionHeader']))
            story.append(Paragraph(self.settings.company_bank_info, self.styles['NormalText']))
            story.append(Spacer(1, 12))
        
        # Terms and conditions
        story.append(Paragraph("Terms & Conditions:", self.styles['SectionHeader']))
        story.append(Paragraph(self.settings.invoice_terms, self.styles['NormalText']))
        
        return story

from datetime import datetime
from app import db


class Payment(db.Model):
    """Partial/full payments recorded against invoices."""

    __tablename__ = 'payments'

    id = db.Column(db.Integer, primary_key=True)
    invoice_id = db.Column(db.Integer, db.ForeignKey('invoices.id'), nullable=False, index=True)
    amount = db.Column(db.Numeric(10, 2), nullable=False)
    currency = db.Column(db.String(3), nullable=True)  # If multi-currency per payment
    payment_date = db.Column(db.Date, nullable=False, default=datetime.utcnow)
    method = db.Column(db.String(50), nullable=True)
    reference = db.Column(db.String(100), nullable=True)
    notes = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    def __repr__(self):
        return f"<Payment {self.amount} for invoice {self.invoice_id}>"


class CreditNote(db.Model):
    """Credit notes issued to offset invoices."""

    __tablename__ = 'credit_notes'

    id = db.Column(db.Integer, primary_key=True)
    invoice_id = db.Column(db.Integer, db.ForeignKey('invoices.id'), nullable=False, index=True)
    credit_number = db.Column(db.String(50), unique=True, nullable=False, index=True)
    amount = db.Column(db.Numeric(10, 2), nullable=False)
    reason = db.Column(db.Text, nullable=True)
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    def __repr__(self):
        return f"<CreditNote {self.credit_number} for invoice {self.invoice_id}>"


class InvoiceReminderSchedule(db.Model):
    """Schedules to send invoice reminders before/after due dates."""

    __tablename__ = 'invoice_reminder_schedules'

    id = db.Column(db.Integer, primary_key=True)
    invoice_id = db.Column(db.Integer, db.ForeignKey('invoices.id'), nullable=False, index=True)
    days_offset = db.Column(db.Integer, nullable=False)  # negative for before due, positive after
    recipients = db.Column(db.Text, nullable=True)  # comma-separated; default to client email if empty
    template_name = db.Column(db.String(100), nullable=True)
    active = db.Column(db.Boolean, default=True, nullable=False)
    last_sent_at = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    def __repr__(self):
        return f"<InvoiceReminderSchedule inv={self.invoice_id} offset={self.days_offset}>"



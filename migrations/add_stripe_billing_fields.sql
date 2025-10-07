-- Migration: Add Stripe Billing Fields
-- Description: Adds billing-related fields to organizations table and creates subscription_events table
-- Date: 2025-10-07

-- Add new billing fields to organizations table
ALTER TABLE organizations 
ADD COLUMN IF NOT EXISTS stripe_price_id VARCHAR(100),
ADD COLUMN IF NOT EXISTS subscription_quantity INTEGER DEFAULT 1 NOT NULL,
ADD COLUMN IF NOT EXISTS next_billing_date TIMESTAMP,
ADD COLUMN IF NOT EXISTS billing_issue_detected_at TIMESTAMP,
ADD COLUMN IF NOT EXISTS last_billing_email_sent_at TIMESTAMP;

-- Update existing stripe_subscription_status column to allow more statuses
COMMENT ON COLUMN organizations.stripe_subscription_status IS 'Subscription status: active, trialing, past_due, canceled, incomplete, incomplete_expired, unpaid';

-- Create subscription_events table
CREATE TABLE IF NOT EXISTS subscription_events (
    id SERIAL PRIMARY KEY,
    organization_id INTEGER NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    
    -- Event details
    event_type VARCHAR(100) NOT NULL,
    event_id VARCHAR(100) UNIQUE,
    
    -- Stripe resource references
    stripe_customer_id VARCHAR(100),
    stripe_subscription_id VARCHAR(100),
    stripe_invoice_id VARCHAR(100),
    stripe_payment_intent_id VARCHAR(100),
    
    -- Event data and status
    status VARCHAR(50),
    previous_status VARCHAR(50),
    quantity INTEGER,
    previous_quantity INTEGER,
    amount NUMERIC(10, 2),
    currency VARCHAR(3),
    
    -- Processing info
    processed BOOLEAN DEFAULT FALSE NOT NULL,
    processing_error TEXT,
    retry_count INTEGER DEFAULT 0 NOT NULL,
    
    -- Full event payload (for debugging)
    raw_payload TEXT,
    
    -- Metadata
    notes TEXT,
    created_by INTEGER REFERENCES users(id),
    
    -- Timestamps
    event_timestamp TIMESTAMP NOT NULL,
    created_at TIMESTAMP DEFAULT NOW() NOT NULL,
    processed_at TIMESTAMP,
    
    -- Indexes for performance
    CONSTRAINT subscription_events_org_id_fkey FOREIGN KEY (organization_id) REFERENCES organizations(id) ON DELETE CASCADE
);

-- Create indexes for subscription_events
CREATE INDEX IF NOT EXISTS idx_subscription_events_org_id ON subscription_events(organization_id);
CREATE INDEX IF NOT EXISTS idx_subscription_events_event_type ON subscription_events(event_type);
CREATE INDEX IF NOT EXISTS idx_subscription_events_event_id ON subscription_events(event_id);
CREATE INDEX IF NOT EXISTS idx_subscription_events_customer_id ON subscription_events(stripe_customer_id);
CREATE INDEX IF NOT EXISTS idx_subscription_events_subscription_id ON subscription_events(stripe_subscription_id);
CREATE INDEX IF NOT EXISTS idx_subscription_events_event_timestamp ON subscription_events(event_timestamp);
CREATE INDEX IF NOT EXISTS idx_subscription_events_processed ON subscription_events(processed) WHERE NOT processed;

-- Add comments to tables and columns for documentation
COMMENT ON TABLE subscription_events IS 'Tracks all Stripe subscription lifecycle events for audit and debugging';
COMMENT ON COLUMN subscription_events.event_type IS 'Type of Stripe event (e.g., invoice.paid, customer.subscription.updated)';
COMMENT ON COLUMN subscription_events.event_id IS 'Unique Stripe event ID';
COMMENT ON COLUMN subscription_events.processed IS 'Whether this event has been successfully processed';
COMMENT ON COLUMN subscription_events.raw_payload IS 'Full JSON payload from Stripe webhook';

COMMENT ON COLUMN organizations.stripe_price_id IS 'Current Stripe price ID being used';
COMMENT ON COLUMN organizations.subscription_quantity IS 'Number of seats/users in subscription';
COMMENT ON COLUMN organizations.next_billing_date IS 'Date of next billing cycle';
COMMENT ON COLUMN organizations.billing_issue_detected_at IS 'Timestamp when payment failure was detected';
COMMENT ON COLUMN organizations.last_billing_email_sent_at IS 'Last time billing notification email was sent (for dunning management)';

-- Migration complete
SELECT 'Stripe billing fields migration completed successfully' AS status;


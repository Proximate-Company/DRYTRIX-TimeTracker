"""
Fix stripe_service.py to add lazy initialization calls
"""
import re

# Read the file
with open('app/utils/stripe_service.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Add self._ensure_initialized() before each "if not self.is_configured():" check
# that doesn't already have it
content = re.sub(
    r'(\n        )(if not self\.is_configured\(\):)',
    r'\1self._ensure_initialized()\n        \2',
    content
)

# Also add it to methods that check organization.stripe_customer_id directly
content = re.sub(
    r'(\n        )(if not organization\.stripe_customer_id:)',
    r'\1self._ensure_initialized()\n        \2',
    content
)

# Write back
with open('app/utils/stripe_service.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("✓ Fixed stripe_service.py")
print("Added lazy initialization calls to all Stripe methods")


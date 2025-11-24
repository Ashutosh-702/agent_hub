"""
Company saver for Apollo integration.
Reuses the same logic as Lusha company saver since the structure is identical.
"""
from integrations.lusha.company_saver import CompanySaver

# Re-export for consistency
__all__ = ['CompanySaver']


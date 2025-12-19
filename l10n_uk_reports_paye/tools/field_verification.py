import re

from odoo import _
from odoo.exceptions import ValidationError

VRN_REGEX = re.compile(r'^V[0-9]{10}[A-HJ-NP-Z]{0,2}$')


def validate_verification_number(vrn):
    """
        Check that the CIS verification number is correct

        Regex: ^V[0-9]{10}[A-HJ-NP-Z]{0,2}$
    """
    if not VRN_REGEX.match(vrn):
        raise ValidationError(_("Invalid CIS Verification Number."))

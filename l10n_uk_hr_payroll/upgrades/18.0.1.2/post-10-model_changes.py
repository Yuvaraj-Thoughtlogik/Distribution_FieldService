# -*- coding:utf-8 -*-
# AUGUR Solutions Payroll Proprietary License v1.0
# Copyright © Augur Solutions Ltd, 2024-2025
#
# The author and owner of this software is Augur Solutions Ltd
# (a company registered in England with registered number 15886736)
# of 15 Roxford Close, Upper Halliford, SURREY TW17 8RS, England
#
# This software and associated files (the “Software”) may only be used (executed, modified, executed after
# modifications) if you have purchased a valid license from the authors, or if you have received a written
# agreement from the authors of the Software.
#
# It is forbidden to publish, distribute, sublicense, or sell copies of the Software or modified copies of the
# Software.
#
# The above copyright notice and this permission notice must be included in all copies or substantial portions of
# the Software.
#
# THE SOFTWARE IS PROVIDED “AS IS”, WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED
# TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL
# THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF
# CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS
# IN THE SOFTWARE.

import logging

_logger = logging.getLogger(__name__)

# Create new fields for name changes in hr_contract
#  is_autoenrollment -> is_autoenrolment
#  next_autoenrollment_date -> next_autoenrolment_date
def migrate(cr, version):
    cr.execute("ALTER TABLE hr_contract ADD COLUMN is_autoenrolment BOOLEAN")
    cr.execute("ALTER TABLE hr_contract ADD COLUMN next_autoenrolment_date DATE")

    cr.execute("UPDATE hr_contract set is_autoenrolment = is_autoenrollment")
    _logger.info("Updated %s contracts", cr.rowcount)

    cr.execute("UPDATE hr_contract set next_autoenrolment_date = next_autoenrollment_date")
    _logger.info("Updated %s contracts", cr.rowcount)
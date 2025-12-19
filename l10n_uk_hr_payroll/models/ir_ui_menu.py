# -*- coding:utf-8 -*-
# AUGUR Solutions Payroll Proprietary License v1.0
# Copyright © Augur Solutions Ltd, 2024-2025

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


from odoo import models


class IrUiMenu(models.Model):
    _inherit = 'ir.ui.menu'

    def _load_menus_blacklist(self):
        res = super()._load_menus_blacklist()
        uk_id = self.env.ref('base.uk', raise_if_not_found=False)
        user_uk_companies = self.env.user.company_ids.filtered(lambda c: c.country_id == uk_id)
        if not user_uk_companies:
            res.append(self.env.ref('l10n_uk_hr_payroll.menu_reporting_l10n_uk').id)
        return res

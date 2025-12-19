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

from datetime import date
from freezegun import freeze_time

from odoo import Command
from odoo.tests.common import TransactionCase


class TestPayrollCommon(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super(TestPayrollCommon, cls).setUpClass()
        with freeze_time('2023-01-01'):
            today = date.today()
            cls.uk_company = cls.env['res.company'].create({
                'name': 'My UK Company - Test',
                'country_id': cls.env.ref('base.uk').id,
                'currency_id': cls.env.ref('base.GBP').id,
                'l10n_uk_company_number': '0477472701',
                'street': 'Paradise Road',
                'zip': 'TW17 8RS',
                'city': 'Upper Halliford',
                'vat': 'GB12345768',
                'phone': '020 1234 5678',
            })

            cls.env.user.company_ids |= cls.uk_company
            cls.env = cls.env(context=dict(cls.env.context, allowed_company_ids=cls.uk_company.ids))

            cls.resource_calendar = cls.env['resource.calendar'].create({
                'name': 'Test Calendar',
                'company_id': cls.uk_company.id,
                'hours_per_day': 7.5,
                'tz': "Europe/London",
                'two_weeks_calendar': False,
                'hours_per_week': 37.5,
                'full_time_required_hours': 37.5
            })

            cls.resource_calendar_9_10 = cls.resource_calendar.copy({
                'name': 'Calendar (9 / 10)',
                'full_time_required_hours': 37.5,
                'attendance_ids': [
                    (0, 0, {'name': 'Monday Morning', 'dayofweek': '0', 'hour_from': 9, 'hour_to': 12,
                            'day_period': 'morning'}),
                    (0, 0, {'name': 'Monday Lunch', 'dayofweek': '0', 'hour_from': 12, 'hour_to': 12.5,
                            'day_period': 'lunch'}),
                    (0, 0, {'name': 'Monday Afternoon', 'dayofweek': '0', 'hour_from': 12.5, 'hour_to': 17,
                            'day_period': 'afternoon'}),
                    (0, 0, {'name': 'Tuesday Morning', 'dayofweek': '1', 'hour_from': 9, 'hour_to': 12,
                            'day_period': 'morning'}),
                    (0, 0, {'name': 'Tuesday Lunch', 'dayofweek': '1', 'hour_from': 12, 'hour_to': 12.5,
                            'day_period': 'lunch'}),
                    (0, 0, {'name': 'Tuesday Afternoon', 'dayofweek': '1', 'hour_from': 12.5, 'hour_to': 17,
                            'day_period': 'afternoon'}),
                    (0, 0, {'name': 'Wednesday Morning', 'dayofweek': '2', 'hour_from': 9, 'hour_to': 12,
                            'day_period': 'morning'}),
                    (0, 0, {'name': 'Wednesday Lunch', 'dayofweek': '2', 'hour_from': 12, 'hour_to': 12.5,
                            'day_period': 'lunch'}),
                    (0, 0, {'name': 'Wednesday Afternoon', 'dayofweek': '2', 'hour_from': 12.5, 'hour_to': 17,
                            'day_period': 'afternoon'}),
                    (0, 0, {'name': 'Thursday Morning', 'dayofweek': '3', 'hour_from': 9, 'hour_to': 12,
                            'day_period': 'morning'}),
                    (0, 0, {'name': 'Thursday Lunch', 'dayofweek': '3', 'hour_from': 12, 'hour_to': 12.5,
                            'day_period': 'lunch'}),
                    (0, 0, {'name': 'Thursday Afternoon', 'dayofweek': '3', 'hour_from': 12.5, 'hour_to': 17,
                            'day_period': 'afternoon'}),
                    (0, 0, {'name': 'Friday Morning', 'dayofweek': '4', 'hour_from': 9, 'hour_to': 12,
                            'day_period': 'morning'}),
                ]
            })

            cls.employee_georges = cls.env['hr.employee'].create({
                'name': 'Georges',
                'private_country_id': cls.env.ref('base.uk').id,
                'resource_calendar_id': cls.resource_calendar.id,
                'company_id': cls.uk_company.id,
                'marital': "single",
            })

            first_contract_georges = cls.env['hr.contract'].create({
                'name': "Georges's contract",
                'employee_id': cls.employee_georges.id,
                'resource_calendar_id': cls.resource_calendar.id,
                'company_id': cls.uk_company.id,
                'structure_type_id': cls.env.ref('hr_contract.structure_type_employee_uk').id,
                'date_start': date(today.year - 2, 1, 1),
                'date_end': date(today.year - 2, 12, 31),
                'wage': 2500.0,
                'hourly_wage': 0.0,
            })

            cls.georges_contracts = first_contract_georges

            cls.georges_contracts |= first_contract_georges.copy({
                'date_start': date(today.year - 1, 1, 1),
                'date_end': date(today.year - 1, 5, 31),
                'resource_calendar_id': cls.resource_calendar_9_10.id,
                'wage': 1250
            })

            cls.georges_contracts |= first_contract_georges.copy({
                'date_start': date(today.year - 1, 6, 1),
                'date_end': date(today.year - 1, 8, 31),
            })

            cls.georges_contracts.write(
                {'state': 'open'})  # By default, the state is 'draft' when we create a new contract

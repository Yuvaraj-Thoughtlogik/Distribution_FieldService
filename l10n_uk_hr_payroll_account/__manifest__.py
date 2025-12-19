# AUGUR Payroll Proprietary License v1.0
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

{
    'name': 'United Kingdom - Payroll with Accounting',
    'countries': ['gb'],
    'category': 'Human Resources/Payroll',
    'depends': [
        'l10n_uk_hr_payroll',
        'hr_payroll_account',
        'l10n_uk',
    ],
    'author': 'Augur Solutions LTD',
    'website': 'https://www.auguraccountants.com/odoo-uk-payroll',
    'version': '18.0.1.1',
    'description': """
Accounting Data for UK Payroll Rules.
=============================================
    """,

    'auto_install': True,
    'data': [
        "data/account_chart_template_data.xml",
        "security/ir.model.access.csv",
    ],
    'demo': [
        "data/l10n_uk_hr_payroll_account_demo.xml",
    ],
    'installable': True,
    'license': 'OPL-1',
}

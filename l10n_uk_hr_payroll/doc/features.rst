.. _features:

UK Payroll Features
===================

In this section, we document some of the features included in UK Payroll.

Payslip Generation
++++++++++++++++++

By default, payslip generation occurs when a payslip has a draft entry created.
However, you might want to draft the payslip/batch and then only send payslips
when the payslip is finalised and paid.

In addition, we calculate Employment Allowance (when this is claimed) on the
payslips so that this can be reclaimed in the EPS submission.  We want to
minimise the change that payslips will be altered once they are sent.

UK Payroll has moved the payslip generation to when a payslip is moved from
draft to paid.

Payslip Selection Criteria
++++++++++++++++++++++++++

There are a number of functions that search for items on payslips and are
used for reporting. e.g. hr_payslip._sum() and hr_payslip._sum_category()

By default, these work on a start date and an optional end date.  Whilst the
YTD reset date is typically set to 6 April in a UK setting, companies may pay
employees on a calendar month basis.  HMRC recognises a pay run being 'in scope'
when the payment date is within the tax year (6 April Y0 -> 5 April Y1)

Therefore, these helper functions have been modified to ensure that amounts are
included in totals in the tax year they were paid in.

Pension Funds
+++++++++++++

It is a requirement in the UK to auto-enroll/re-enroll employees every three years.
Employees may opt-out, but it is a responsibility of the employer to keep track of
re-enrolment dates.  The re-enrolment date is held for each contract.

Pension funds are configurable in their own screen by administrators who are able to
access it via Configuration->United Kingdom->Pension Funds

Pension funds configured in this way can be configured as Relief at Source or
Direct Pay.  Employee contributions that are made with Relief at Source are
reduced by 20% and the relief is paid in to the pension fund.

For example, if the employees contribution is 5%, then 4% is deducted (5% * (100%-20%)
automatically.

Multiple pension funds may be configured and allocated on a contract by contract basis.

Employment Allowance
++++++++++++++++++++



Small Employers Relief
++++++++++++++++++++++


Company Directors
+++++++++++++++++



HMRC Real Time Interface (RTI) Reporting
++++++++++++++++++++++++++++++++++++++++
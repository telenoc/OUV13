# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.tools.misc import format_date


class ReportPartnerLedger(models.AbstractModel):
    _inherit = "account.partner.ledger"

    @api.model
    def _get_partner_ledger_lines(self, options, line_id=None):
        res = super(ReportPartnerLedger, self)._get_partner_ledger_lines(options, line_id)
        for i in res:
            i['columns'][2]['class'] = 'limit_width'
            print("ssssssssssss:", i['columns'][2])
        print("wwwwwwwwwwww", res[1])
        return res

    def _get_columns_name(self, options):
        columns = [
            {},
            {'name': _('JRNL')},
            {'name': _('Account')},
            {'name': _('Ref'), 'max-width': '20px'},
            {'name': _('Due Date'), 'class': 'date'},
            {'name': _('Matching Number')},
            {'name': _('Initial Balance'), 'class': 'number'},
            {'name': _('Debit'), 'class': 'number'},
            {'name': _('Credit'), 'class': 'number'}]

        if self.user_has_groups('base.group_multi_currency'):
            columns.append({'name': _('Amount Currency'), 'class': 'number'})

        columns.append({'name': _('Balance'), 'class': 'number'})

        return columns

    # {'name': _('JRNL'), 'style': {'max-width': '10%', 'width': '10%'}},
    # {'name': _('Account'), 'style': {'max-width': '10%', 'width': '10%'}},
    # {'name': _('Ref'), 'style': {'max-width': '10%', 'width': '10%'}},
    # {'name': _('Due Date'), 'class': 'date', 'style': {'max-width': '10%', 'width': '10%'}},
    # {'name': _('Matching Number'), 'style': {'max-width': '10%', 'width': '10%'}},
    # {'name': _('Initial Balance'), 'class': 'number', 'style': {'max-width': '10%', 'width': '10%'}},
    # {'name': _('Debit'), 'class': 'number', 'style': {'max-width': '10%', 'width': '10%'}},
    # {'name': _('Credit'), 'class': 'number', 'style': {'max-width': '10%', 'width': '10%'}}]

    @api.model
    def _get_query_amls(self, options, expanded_partner=None, offset=None, limit=None):
        ''' Construct a query retrieving the account.move.lines when expanding a report line with or without the load
        more.
        :param options:             The report options.
        :param expanded_partner:    The res.partner record corresponding to the expanded line.
        :param offset:              The offset of the query (used by the load more).
        :param limit:               The limit of the query (used by the load more).
        :return:                    (query, params)
        '''
        unfold_all = options.get('unfold_all') or (self._context.get('print_mode') and not options['unfolded_lines'])

        # Get sums for the account move lines.
        # period: [('date' <= options['date_to']), ('date', '>=', options['date_from'])]
        if expanded_partner:
            domain = [('partner_id', '=', expanded_partner.id)]
        elif unfold_all:
            domain = []
        elif options['unfolded_lines']:
            domain = [('partner_id', 'in', [int(line[8:]) for line in options['unfolded_lines']])]

        new_options = self._get_options_sum_balance(options)
        tables, where_clause, where_params = self._query_get(new_options, domain=domain)
        ct_query = self._get_query_currency_table(options)

        query = '''
                SELECT
                    account_move_line.id,
                    account_move_line.date,
                    account_move_line.date_maturity,
                    account_move_line.name,
                    account_move_line.ref,
                    account_move_line.company_id,
                    account_move_line.account_id,             
                    account_move_line.payment_id,
                    account_move_line.partner_id,
                    account_move_line.currency_id,
                    account_move_line.amount_currency,
                    ROUND(account_move_line.debit * currency_table.rate, currency_table.precision)   AS debit,
                    ROUND(account_move_line.credit * currency_table.rate, currency_table.precision)  AS credit,
                    ROUND(account_move_line.balance * currency_table.rate, currency_table.precision) AS balance,
                    account_move_line__move_id.name         AS move_name,
                    company.currency_id                     AS company_currency_id,
                    partner.name                            AS partner_name,
                    account_move_line__move_id.type         AS move_type,
                    account.code                            AS account_code,
                    account.name                            AS account_name,
                    journal.code                            AS journal_code,
                    journal.name                            AS journal_name,
                    full_rec.name                           AS full_rec_name
                FROM account_move_line
                LEFT JOIN account_move account_move_line__move_id ON account_move_line__move_id.id = account_move_line.move_id
                LEFT JOIN %s ON currency_table.company_id = account_move_line.company_id
                LEFT JOIN res_company company               ON company.id = account_move_line.company_id
                LEFT JOIN res_partner partner               ON partner.id = account_move_line.partner_id
                LEFT JOIN account_account account           ON account.id = account_move_line.account_id
                LEFT JOIN account_journal journal           ON journal.id = account_move_line.journal_id
                LEFT JOIN account_full_reconcile full_rec   ON full_rec.id = account_move_line.full_reconcile_id
                WHERE %s
                ORDER BY account_move_line.date asc
            ''' % (ct_query, where_clause)

        if offset:
            query += ' OFFSET %s '
            where_params.append(offset)
        if limit:
            query += ' LIMIT %s '
            where_params.append(limit)

        return query, where_params

    # @api.model
    # def _get_report_line_move_line(self, options, partner, aml, cumulated_init_balance, cumulated_balance):
    #     if aml['payment_id']:
    #         caret_type = 'account.payment'
    #     elif aml['move_type'] in ('in_refund', 'in_invoice', 'in_receipt'):
    #         caret_type = 'account.invoice.in'
    #     elif aml['move_type'] in ('out_refund', 'out_invoice', 'out_receipt'):
    #         caret_type = 'account.invoice.out'
    #     else:
    #         caret_type = 'account.move'
    #
    #     date_maturity = aml['date_maturity'] and format_date(self.env, fields.Date.from_string(aml['date_maturity']))
    #     if aml['ref']:
    #         ref_description = str(aml['name']) + str(aml['ref'])
    #     else:
    #         ref_description = str(aml['name'])
    #     columns = [
    #         {'name': aml['journal_code']},
    #         {'name': aml['account_code']},
    #         {'name': ref_description},
    #         {'name': date_maturity or '', 'class': 'date'},
    #         {'name': aml['full_rec_name'] or ''},
    #         {'name': self.format_value(cumulated_init_balance), 'class': 'number'},
    #         {'name': self.format_value(aml['debit'], blank_if_zero=True), 'class': 'number'},
    #         {'name': self.format_value(aml['credit'], blank_if_zero=True), 'class': 'number'},
    #     ]
    #     if self.user_has_groups('base.group_multi_currency'):
    #         if aml['currency_id']:
    #             currency = self.env['res.currency'].browse(aml['currency_id'])
    #             formatted_amount = self.format_value(aml['amount_currency'], currency=currency, blank_if_zero=True)
    #             columns.append({'name': formatted_amount, 'class': 'number'})
    #         else:
    #             columns.append({'name': ''})
    #     columns.append({'name': self.format_value(cumulated_balance), 'class': 'number'})
    #     return {
    #         'id': aml['id'],
    #         'parent_id': 'partner_%s' % partner.id,
    #         'name': format_date(self.env, aml['date']),
    #         'class': 'date',
    #         'columns': columns,
    #         'caret_options': caret_type,
    #         'level': 4,
    #     }


class AccountReport(models.AbstractModel):
    _inherit = 'account.report'

    @api.model
    def _format_aml_name(self, line_name, move_ref, move_name):
        ''' Format the display of an account.move.line record. As its very costly to fetch the account.move.line
        records, only line_name, move_ref, move_name are passed as parameters to deal with sql-queries more easily.

        :param line_name:   The name of the account.move.line record.
        :param move_ref:    The reference of the account.move record.
        :param move_name:   The name of the account.move record.
        :return:            The formatted name of the account.move.line record.
        '''
        names = []
        if move_name != '/':
            names.append(move_name)
        if move_ref and move_ref != '/':
            names.append(move_ref)
        if line_name and line_name != '/':
            names.append(line_name)
        name = '-'.join(names)
        # TODO: check if no_format is still needed
        # if len(name) > 35 and not self.env.context.get('no_format'):
        #     name = name[:32] + "..."
        return name

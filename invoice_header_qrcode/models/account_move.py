# -*- coding: utf-8 -*-

try:
    import qrcode
except ImportError:
    qrcode = None
try:
    import base64
except ImportError:
    base64 = None
from io import BytesIO

from odoo import models, fields, api, _


class AccountMove(models.Model):
    _inherit = 'account.move'

    qr_code = fields.Binary(string="QR Code", compute='generate_qrcode')

    @api.depends('name', 'partner_id', 'invoice_date', 'amount_untaxed', 'amount_total', 'amount_by_group')
    def generate_qrcode(self):
        if qrcode and base64:
            if self.name:
                lst = []
                if self.amount_by_group:
                    for i in self.amount_by_group:
                        lst.append(i[1])
                qr = qrcode.QRCode(
                    version=1,
                    error_correction=qrcode.constants.ERROR_CORRECT_L,
                    box_size=12,
                    border=4,
                )
                values = {
                    'company': self.company_id.name,
                    'Invoice number': self.name,
                    'Partner Name': self.partner_id.name,
                    'Invoice Date': self.invoice_date,
                    'Untaxed Amount': self.amount_untaxed,
                    'Total Amount': self.amount_total,
                    'VAT': sum(lst),
                }
                qr.add_data(values)
                qr.make(fit=True)
                img = qr.make_image()
                temp = BytesIO()
                img.save(temp, format="PNG")
                qr_image = base64.b64encode(temp.getvalue())
                self.write({'qr_code': qr_image})

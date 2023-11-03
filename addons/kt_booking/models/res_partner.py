from odoo import api, fields, models


class ResPartner(models.Model):
    _inherit = 'res.partner'

    partner_type = fields.Selection([
        ('customer', 'customer'),
        ('driver', 'Driver'),
    ], default="customer")

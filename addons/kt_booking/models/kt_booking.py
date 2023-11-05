from odoo import api, fields, models, _
from odoo.exceptions import UserError


class KtBooking(models.Model):
    _name = 'kt.booking'
    _description = 'Kt Booking'
    _rec_name = "customer_id"
    _order = "create_date"

    customer_id = fields.Many2one('res.partner', required=True)
    start_latitude = fields.Float('Latitude', digits=(10, 6))
    start_longitude = fields.Float('Longitude', digits=(10, 6))
    start_kilo = fields.Float('Start Kilo')
    driver_id = fields.Many2one('res.partner')
    driver_phone = fields.Char(related="driver_id.phone")
    end_kilo = fields.Float('End Kilo')
    currency_id = fields.Many2one('res.currency', default=lambda self: self.env.company.currency_id)
    amount = fields.Monetary(currency_field='currency_id',
                             string="Total Amount", )  # compute="_compute_total_amount", inverse="_inverse_end_kilo",
    # string="Total Amount")
    service_fees = fields.Monetary(currency_field='currency_id')  # , compute="_compute_total_amount", store=True)
    driver_fees = fields.Monetary(currency_field='currency_id')  # , compute="_compute_total_amount", store=True)
    account_move_id = fields.Many2one('account.move')
    active = fields.Boolean(default=True)

    state = fields.Selection([
        ('draft', 'Draft'),
        ('booking', 'Booking'),
        ('accept', 'Accept'),
        ('reach_to_customer', 'Reach to Customer'),
        ('arrived', 'Arrived'),
        ('paid', 'paid'),
        ('cancel', 'Cancel'),
    ], default='draft')

    # @api.depends('start_kilo', 'end_kilo')
    # def _compute_total_amount(self):
    #     # TODO:change make_arrived method in add remove compute
    #     for rec in self:
    #         ICPSudo = self.env['ir.config_parameter'].sudo()
    #         per_kilo_fees = float(ICPSudo.get_param('per_kilo_fees'))
    #         service_fees = float(ICPSudo.get_param('service_fees'))
    #         if rec.end_kilo:
    #             rec.amount = rec.end_kilo * per_kilo_fees
    #             rec.service_fees = rec.end_kilo * service_fees
    #             rec.driver_fees = rec.amount - rec.service_fees
    #         else:
    #             rec.amount = rec.start_kilo * per_kilo_fees
    #             rec.service_fees = rec.start_kilo * service_fees
    #             rec.driver_fees = rec.amount - rec.service_fees

    # def _inverse_end_kilo(self):
    #     for rec in self:
    #         rec.end_kilo = rec.start_kilo + (rec.amount / 2)

    @api.model
    def is_allowed_transition(self, old_state, new_state):
        allowed = [
            ('draft', 'booking'),
            ('booking', 'cancel'),
            ('booking', 'accept'),
            ('accept', 'cancel'),
            ('accept', 'reach_to_customer'),
            ('reach_to_customer', 'arrived'),
            ('reach_to_customer', 'cancel'),
            ('arrived', 'paid'),
            # TODO:Test
            ('cancel', 'draft'),
            ('arrived', 'draft'),
            ('paid', 'draft'),
        ]
        return (old_state, new_state) in allowed

    def change_state(self, new_state):
        for rec in self:
            if rec.is_allowed_transition(rec.state, new_state):
                rec.state = new_state
            else:
                msg = _('Moving from %s to %s is is not allowed') % (rec.state, new_state)
                raise UserError(msg)

    def rest_to_draft(self):
        self.change_state('draft')

    def make_booking(self):
        self.change_state('booking')

    def make_accept(self):
        partner_id = self.env.user.partner_id
        if partner_id.partner_type == "driver":
            self.sudo().driver_id = partner_id
        if not self.driver_id:
            raise UserError(_("Driver should be added First."))

        self.change_state('accept')

    def make_reach_to_customer(self):
        ICPSudo = self.env['ir.config_parameter'].sudo()
        self.start_kilo = ICPSudo.get_param('init_kilo')
        self.change_state('reach_to_customer')

    def make_arrived(self):
        if not self.end_kilo:
            raise UserError(_("End Kilo should be added First."))
        if self.start_kilo >= self.end_kilo:
            raise UserError(_("End should be greater than Start Kilo."))

        ICPSudo = self.env['ir.config_parameter'].sudo()
        per_kilo_fees = float(ICPSudo.get_param('per_kilo_fees'))
        if self.end_kilo:
            self.amount = self.end_kilo * per_kilo_fees
        else:
            self.amount = self.start_kilo * per_kilo_fees
        self.change_state('arrived')

    def make_cancel(self):
        self.change_state('cancel')

    def make_paid(self):
        ICPSudo = self.env['ir.config_parameter'].sudo()
        service_fees = float(ICPSudo.get_param('service_fees'))
        self.service_fees = self.start_kilo * service_fees
        self.driver_fees = self.amount - self.service_fees
        # TODO:create invoice
        self._create_invoice()
        self.change_state('paid')

    def _create_invoice(self):
        invoice_create_data = {
            'move_type': 'out_invoice',

            'partner_id': 10,

            'invoice_date': fields.Date.today(),
            'invoice_line_ids': [
                (0, 0, {
                    "product_id": self.env.ref('kt_booking.kali_taxi_product_product').id,
                    "quantity": 1,
                    "price_unit": self.service_fees,
                    "currency_id": 1,
                    "display_type": "product",
                    "tax_ids":False
                })
            ]
        }
        account_move_id = self.env['account.move'].create(invoice_create_data)
        account_move_id.action_post()
        self.account_move_id = account_move_id

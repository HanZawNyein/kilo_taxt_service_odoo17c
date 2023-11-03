from odoo import api, fields, models, _
from odoo.exceptions import UserError


class KtBooking(models.Model):
    _name = 'kt.booking'
    _description = 'Kt Booking'
    _rec_name = "customer_id"

    customer_id = fields.Many2one('res.partner')
    start_latitude = fields.Float('Latitude', digits=(10, 6))
    start_longitude = fields.Float('Longitude', digits=(10, 6))
    start_kilo = fields.Float('Start Kilo')
    driver_id = fields.Many2one('res.partner')
    end_kilo = fields.Float('End Kilo')
    currency_id = fields.Many2one('res.currency', default=lambda self: self.env.company.currency_id)
    amount = fields.Monetary(currency_field='currency_id', compute="")
    state = fields.Selection([
        ('draft', 'Draft'),
        ('booking', 'Booking'),
        ('arrived', 'Arrived'),
        ('cancel', 'Cancel'),
    ], default='draft')

    @api.depends('start_kilo', 'end_kilo')
    def _compute_amount(self):
        for rec in self:
            total_kilo = rec.end_kilo - rec.start_kilo
            total_kilo *= 300  # 300MMK
            rec.amount = total_kilo

    @api.model
    def is_allowed_transition(self, old_state, new_state):
        allowed = [
            ('draft', 'booking'),
            ('booking', 'cancel'),
            ('booking', 'arrived'),
            ('cancel', 'draft'),
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

    def make_arrived(self):
        self.change_state('arrived')

    def make_cancel(self):
        self.change_state('cancel')

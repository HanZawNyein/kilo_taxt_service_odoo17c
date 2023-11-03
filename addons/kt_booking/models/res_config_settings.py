from odoo import fields, models, api


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    """
    init_kilo = 1500
    one_kilo_fees = 500
    service_fees = 100

    Example :
    end_kilo = 2500
    total_amount = end_kilo * one_kilo_fees
    total_amount = 2500 * 500 = 1250000

    # owner get
    service_fees_amount = end_kilo * services_fees
    service_fees_amount = 2500*100 = 250000

    # driver get
    driver_one_kilo_fees = one_kilo_fees - service_fees
    driver_one_kilo_fees = 500 -100 = 400

    #
    driver_fees_amount = end_kilo*driver_one_kilo_fees
    driver_fees_amount = 2500*400 = 1000000

    # other way of driver get
    total_amount - service_fees_amount = driver_fees_amount
    1250000 - 250000 =1000000
    """

    init_kilo = fields.Float(string='Init Kilo', config_parameter='init_kilo', default=1500)
    per_kilo_fees = fields.Float(config_parameter='per_kilo_fees')
    service_fees = fields.Float(config_parameter='service_fees')

    @api.model
    def get_values(self):
        res = super(ResConfigSettings, self).get_values()
        ICPSudo = self.env['ir.config_parameter'].sudo()
        res.update(**{
            "init_kilo": ICPSudo.get_param('init_kilo'),
            "per_kilo_fees": ICPSudo.get_param('per_kilo_fees'),
            "service_fees": ICPSudo.get_param('service_fees'),
        })
        return res

from odoo import models, fields, api


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    is_quote_request = fields.Boolean(
        string='Website Quote Request',
        default=False,
    )

    website_quote_feedback = fields.Text(
        string='Website Quote Feedback'
    )

    def action_confirm(self):
        result = super().action_confirm()

        for record in self:
            print("\n\nConfirmed Sales Order:", record.name)
            print("Customer:", record.partner_id.name)
            print("State:", record.state)

        return result
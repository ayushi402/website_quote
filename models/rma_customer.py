from odoo import models, fields


class RmaCustomer(models.Model):
    _name = 'rma.customer'
    _inherit = ['mail.thread','mail.activity.mixin']

    name = fields.Char(string='Name', required=True, tracking=True)
    order = fields.Many2one('sale.order', string='Order', tracking=True)
    date = fields.Date(string='Date', tracking=True)
    customer = fields.Many2one('res.partner', string='Customer', tracking=True)
    product = fields.Many2one('product.product', string='Product', tracking=True)
    return_quantity = fields.Float(string='Return Quantity', tracking=True)
    reason = fields.Text(string='Reason', tracking=True)
    remarks = fields.Text(string='Remarks', tracking=True)
    status = fields.Many2one('rma.status', string='Status', tracking=True)
    return_request_type = fields.Many2one('rma.request.type', string='Return Request Type', tracking=True)
    resolve_date = fields.Date(string='Resolve Date', tracking=True)
    customer_consent = fields.Boolean(string='Customer Consent', tracking=True)
    invoice_issue = fields.Boolean(string='Invoice Issue', tracking=True)
    product_received = fields.Boolean(string='Product Received', tracking=True)
    currency = fields.Many2one('res.currency', string='Currency', tracking=True)
    amount = fields.Float(string='Amount', tracking=True)
    tax_ids = fields.Float(string='Tax', tracking=True)
    full_refund = fields.Boolean(string='Full Refund', tracking=True)


class RmaStatus(models.Model):
    _name = 'rma.status'

    name = fields.Char(string='Name', required=True)
    color = fields.Char(string='Color')
    sequence = fields.Integer(string='Sequence')

class RmaRequestType(models.Model):
    _name = 'rma.request.type'

    name = fields.Char(string='Name', required=True)
    sequence = fields.Integer(string='Sequence')

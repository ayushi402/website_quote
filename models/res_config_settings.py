from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    disable_checkout = fields.Boolean(
        string='Disable Proceed Checkout',
        default=False,
        config_parameter='website_quote.disable_checkout',
        help="Disallow proceeding to checkout from the website order overview.",
    )

    repair_management = fields.Boolean(
        string='Repair Management',
        default=False,
        config_parameter='rma.repair_management',
        help='Allow repair of products returned through RMA.',
    )

    quote_cancel = fields.Boolean(
        string='Quotes Cancellation',
        default=False,
        config_parameter='rma.quote_cancel',
        help='Allow cancellation before quotation confirmation.',
    )

    show_rma_stage_customer = fields.Boolean(
        string='Show RMA Stages to Customer',
        default=True,
        config_parameter='rma.show_rma_stage_customer',
        help='Allow customers to see their RMA status on the website.',
    )

    # Return Policy
    return_days = fields.Integer(
        string='Return Period',
        default=15,
        config_parameter='rma.return_days',
    )

    return_date_basis = fields.Selection(
        selection=[
            ('delivery', 'Delivery Date'),
            ('order', 'Order Date'),
        ],
        string='Return Date Basis',
        default='delivery',
        config_parameter='rma.return_date_basis',
    )

    allow_return_per_order_line = fields.Boolean(
        string='Allow Product Return per Order Line',
        default=True,
        config_parameter='rma.allow_return_per_order_line',
        help='Show a return option for each eligible order line.',
    )

    disable_return_once_rma_generated = fields.Boolean(
        string='Disable Return Once RMA Generated',
        default=False,
        config_parameter='rma.disable_return_once_rma_generated',
        help='Hide the return option after an RMA has been generated for an order.',
    )

    # RMA Mail Notifications
    enable_rma_admin_notification = fields.Boolean(
        string='Enable Notification for Admin',
        default=True,
        config_parameter='rma.enable_admin_notification',
        help='Send RMA notifications to the administrator by email.',
    )

    rma_admin_email_template_id = fields.Many2one(
        'mail.template',
        string='Admin Email Template',
        config_parameter='rma.admin_email_template_id',
        domain=[('model', '=', 'rma.request')],
    )

    enable_rma_customer_notification = fields.Boolean(
        string='Enable Notification for Customer',
        default=True,
        config_parameter='rma.enable_customer_notification',
        help='Send RMA notifications to the customer by email.',
    )

    rma_customer_email_template_id = fields.Many2one(
        'mail.template',
        string='Customer Email Template',
        config_parameter='rma.customer_email_template_id',
        domain=[('model', '=', 'rma.request')],
    )




# class ResConfigSettings(models.TransientModel):
#     _inherit = 'res.config.settings'
#
#     disable_checkout = fields.Boolean(
#         string='Disable Proceed Checkout',
#         default=False,
#         config_parameter='website_quote.disable_checkout',
#         help="Disallow proceed checkout in the order overview page on the website",
#     )
#     repair_management = fields.Boolean(
#         string='Repair Management',
#         default=False,
#         config_parameter='rma.repair_management',
#         help="allow repair the products"
#     )
#     quote_cancel = fields.Boolean(
#         string='Quote Cancel',
#         default=False,
#         config_parameter='rma.quote_cancel',
#         help="allow cancellation before quote confirmation"
#     )
#     show_rma_stage_customer = fields.Boolean(
#         string='Show RMA Stage Customer',
#         default=False,
#         config_parameter='rma.show_rma_stage_customer',
#         help="Enable this if you want to show return stage to customer"
#     )

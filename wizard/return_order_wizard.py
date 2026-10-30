from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class ReturnOrderDetail(models.TransientModel):
	_name = "return.order.detail"
	_description = "Return Order Wizard"

	sale_order_id = fields.Many2one(
		'sale.order',
		string='Sales Order',
		required=True,
		readonly=True,
	)
	request_type_id = fields.Many2one(
		'rma.request.type',
		string='Request Type',
		required=True,
	)
	product_id = fields.Many2one(
		'product.product',
		string='Product',
		required=True,
	)
	product_qty = fields.Float(
		string='Delivered Quantity',
		readonly=True,
	)
	return_quantity = fields.Float(
		string='Return Quantity',
		required=True,
	)
	reason = fields.Text(string='Reason', required=True)


	@api.onchange('product_id', 'sale_order_id')
	def _onchange_product_id(self):
		for wizard in self:
			wizard.product_qty = 0.0

			if wizard.sale_order_id and wizard.product_id:
				lines = wizard.sale_order_id.order_line.filtered(
					lambda line: line.product_id == wizard.product_id
								 and not line.display_type
				)
				wizard.product_qty = sum(lines.mapped('qty_delivered'))


	def action_submit_return(self):
		self.ensure_one()

		order = self.sale_order_id
		partner = self.env.user.partner_id

		if order.partner_id.commercial_partner_id != partner.commercial_partner_id:
			raise ValidationError(_("You cannot return products from this order."))

		if order.state != 'sale':
			raise ValidationError(_("Only confirmed sales orders can be returned."))

		if self.return_quantity <= 0:
			raise ValidationError(_("Return quantity must be greater than zero."))

		order_lines = order.order_line.filtered(
			lambda line: line.product_id == self.product_id
						 and not line.display_type
		)
		delivered_qty = sum(order_lines.mapped('qty_delivered'))

		if delivered_qty <= 0:
			raise ValidationError(_("This product has no delivered quantity."))

		# Basic check only; cumulative previous returns must also be checked
		# before using this in production.
		if self.return_quantity > delivered_qty:
			raise ValidationError(
				_("Return quantity cannot exceed the delivered quantity.")
			)

		print('return order created................')

		return self.env['rma.customer'].create({
			'name': self.env['ir.sequence'].next_by_code('rma.customer') or _('New'),
			'order': order.id,
			'date': fields.Date.today(),
			'customer': partner.id,
			'product': self.product_id.id,
			'return_quantity': self.return_quantity,
			'reason': self.reason,
			'return_request_type': self.request_type_id.id,
			'customer_consent': True,
		})


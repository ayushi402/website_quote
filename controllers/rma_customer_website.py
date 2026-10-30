import logging

from odoo import http, fields
from odoo.exceptions import ValidationError
from odoo.http import request
from odoo.addons.portal.controllers.portal import CustomerPortal

_logger = logging.getLogger(__name__)


class RmaCustomerWebsite(CustomerPortal):

	def _prepare_home_portal_values(self, counters):
		values = super()._prepare_home_portal_values(counters)
		if 'return_count' in counters:
			values['return_count'] = request.env['rma.customer'].sudo().search_count([
				('customer', '=', request.env.user.partner_id.id),
			])
		return values

	def _return_order_form_error(self, order_id, message, post=None):
		if order_id:
			sale_order = request.env['sale.order'].sudo().browse(int(order_id)).exists()
			if sale_order:
				return request.render(
					'website_quote.portal_return_order_page',
					{
						'sale_order': sale_order,
						'return_types': request.env['rma.request.type'].sudo().search([]),
						'return_reasons': False,
						'return_policy': False,
						'form_data': post or {},
						'error_message': message,
					},
				)
		return request.redirect('/my/return-orders')

	def _post_rma_chatter(self, rma, action, customer_name, reference, feedback):
		if not rma or not rma.exists():
			return

		reference = reference or rma.name or 'N/A'
		feedback = feedback or rma.reason or 'No feedback provided.'
		title = 'Website Return Request Submitted' if action == 'create' else 'Website Return Request Updated'
		datetime_value = fields.Datetime.now().strftime('%Y-%m-%d %H:%M:%S')
		body = (
			f'<b>{title}</b><br/>'
			f'Reference: {reference}<br/>'
			f'Feedback: {feedback}<br/>'
			f'Customer: {customer_name}<br/>'
			f'Date: {datetime_value}'
		)
		if action == 'update':
			current_reference = rma.name or 'N/A'
			current_feedback = rma.reason or 'No feedback provided.'
			if current_reference == reference and current_feedback == feedback:
				return
		rma.message_post(body=body, message_type='comment', subtype_xmlid='mail.mt_comment')

	@http.route('/my/return-orders', type='http', auth='user', website=True)
	def portal_return_orders(self, **kw):
		partner = request.env.user.partner_id
		rma_obj = request.env['rma.customer'].sudo().search([('customer', '=', partner.id)])
		return request.render('website_quote.portal_return_orders', {
			'rmas': rma_obj,
		})

	@http.route('/my/return-orders/new', type='http', auth='user', website=True, methods=['GET'])
	def portal_return_order_new(self, **kw):
		sale_order_id = kw.get('sale_order_id') or request.params.get('sale_order_id')
		if not sale_order_id or not str(sale_order_id).isdigit():
			return request.redirect('/my/return-orders')

		partner = request.env.user.partner_id
		sale_order = request.env['sale.order'].sudo().browse(int(sale_order_id)).exists()

		if (
			not sale_order
			or sale_order.partner_id.commercial_partner_id != partner.commercial_partner_id
			or sale_order.state != 'sale'
		):
			return request.redirect('/my')

		if not sale_order.picking_ids.filtered(lambda picking: picking.state == 'done'):
			return request.redirect('/my')

		request_types = request.env['rma.request.type'].sudo().search([])
		return request.render(
			'website_quote.portal_return_order_page',
			{
				'sale_order': sale_order,
				'return_types': request_types,
				'return_reasons': False,
				'return_policy': False,
			},
		)

	@http.route('/my/return-orders/<int:rma_id>/edit', type='http', auth='user', website=True, methods=['GET'])
	def portal_return_order_edit(self, rma_id, **kw):
		partner = request.env.user.partner_id
		rma = request.env['rma.customer'].sudo().browse(rma_id)
		if not rma.exists() or (rma.customer and rma.customer.id != partner.id):
			return request.redirect('/my/return-orders')
		if rma.order and rma.order.partner_id.commercial_partner_id != partner.commercial_partner_id:
			return request.redirect('/my/return-orders')
		request_types = request.env['rma.request.type'].sudo().search([])
		return request.render(
			'website_quote.portal_return_order_page',
			{
				'sale_order': rma.order,
				'return_types': request_types,
				'return_reasons': False,
				'return_policy': False,
				'rma': rma,
			},
		)

	@http.route('/my/return-orders/<int:rma_id>', type='http', auth='user', website=True, methods=['GET'])
	def portal_return_order_detail(self, rma_id, **kw):
		# import pdb; pdb.set_trace()
		partner = request.env.user.partner_id
		rma = request.env['rma.customer'].sudo().browse(rma_id)
		if not rma.exists() or (rma.customer and rma.customer.id != partner.id):
			return request.redirect('/my/return-orders')
		if rma.order and rma.order.partner_id.commercial_partner_id != partner.commercial_partner_id:
			return request.redirect('/my/return-orders')
		return request.render('website_quote.portal_return_order_detail', {
			'rma': rma,
		})

	@http.route('/my/return-orders/submit', type='http', auth='user', website=True, methods=['POST'], csrf=True)
	def portal_return_order_submit(self, **post):
		post = request.httprequest.form.to_dict() or post
		partner = request.env.user.partner_id

		rma_id = post.get('rma_id')
		order_id = post.get('order_id') or post.get('order')
		consent = post.get('customer_consent') or post.get('agree_return_policy')
		customer_consent = consent in ('1', 'true', 'True', 'on', True)
		submitted_customer_id = post.get('customer') or partner.id

		if not order_id or not str(order_id).isdigit():
			return self._return_order_form_error(False, 'The sales order is missing or invalid.', post)

		order = request.env['sale.order'].sudo().browse(int(order_id))
		if not order.exists() or order.partner_id.commercial_partner_id != partner.commercial_partner_id:
			return self._return_order_form_error(False, 'You cannot submit a return request for this order.', post)
		if order.state != 'sale':
			return self._return_order_form_error(order.id, 'Only confirmed sales orders can be returned.', post)
		if not order.picking_ids.filtered(lambda picking: picking.state == 'done'):
			return self._return_order_form_error(order.id, 'This order has no delivered products to return.', post)
		if not customer_consent:
			return self._return_order_form_error(order.id, 'You must confirm the return information before submitting.', post)

		try:
			submitted_customer = int(submitted_customer_id) if submitted_customer_id and str(submitted_customer_id).isdigit() else partner.id
		except (TypeError, ValueError):
			submitted_customer = partner.id
		if submitted_customer != partner.id:
			return self._return_order_form_error(order.id, 'You can only submit returns for your own account.', post)

		selected_rows = []
		for line in order.order_line.filtered(lambda l: not l.display_type and l.product_id.type != 'service'):
			qty_key = f'return_qty_{line.id}'
			qty_value = post.get(qty_key)
			if qty_value is None:
				continue
			try:
				qty = float(qty_value)
			except (TypeError, ValueError):
				continue
			max_allowed = float(line.qty_delivered or line.product_uom_qty or 0)
			if 0 < qty <= max_allowed:
				selected_rows.append({
					'line': line,
					'qty': qty,
					'request_type_id': post.get(f'return_type_{line.id}') or post.get('return_request_type'),
					'reason': (post.get(f'reason_{line.id}') or post.get('reason') or '').strip(),
					'remarks': (post.get(f'remarks_{line.id}') or post.get('remarks') or '').strip(),
				})

		if not selected_rows:
			return self._return_order_form_error(order.id, 'Please select at least one product to return.', post)

		created_rmas = []
		sequence = request.env['ir.sequence'].sudo().search([('code', '=', 'rma.customer')], limit=1)
		for row in selected_rows:
			line = row['line']
			product = line.product_id
			return_qty = float(row['qty'])
			request_type_id = row['request_type_id']
			reason = row['reason']
			remarks = row['remarks']
			if return_qty <= 0:
				continue
			max_allowed = float(line.qty_delivered or line.product_uom_qty or 0)
			if return_qty > max_allowed:
				return self._return_order_form_error(order.id, f'The return quantity for {product.display_name} exceeds the delivered quantity.', post)
			if not request_type_id or not str(request_type_id).isdigit():
				return self._return_order_form_error(order.id, f'Please select a return request type for {product.display_name}.', post)
			if not reason:
				return self._return_order_form_error(order.id, f'Please provide a reason for {product.display_name}.', post)

			request_type = request.env['rma.request.type'].sudo().browse(int(request_type_id))
			if not request_type.exists():
				return self._return_order_form_error(order.id, f'The selected return request type for {product.display_name} is invalid.', post)

			previous_returns = request.env['rma.customer'].sudo().search([
				('order', '=', order.id),
				('product', '=', product.id),
			])
			prev_qty = float(sum(previous_returns.filtered(lambda rec: rec.id != (int(rma_id) if rma_id and str(rma_id).isdigit() else False)).mapped('return_quantity') or [0.0]))
			if return_qty + prev_qty > max_allowed:
				return self._return_order_form_error(order.id, f'The total return quantity for {product.display_name} exceeds the delivered quantity.', post)

			request_ref = sequence and sequence.next_by_code('rma.customer') or f'RMA-{fields.Date.today().strftime("%Y%m%d")}-{order.id}'
			vals = {
				'name': request_ref,
				'order': order.id,
				'date': fields.Date.today(),
				'customer': partner.id,
				'product': product.id,
				'return_quantity': return_qty,
				'reason': reason,
				'remarks': remarks,
				'return_request_type': request_type.id,
				'customer_consent': customer_consent,
			}
			try:
				rma = request.env['rma.customer'].sudo().create(vals)
			except ValidationError as exc:
				return self._return_order_form_error(order.id, str(exc), post)
			except Exception as exc:
				request.env.cr.rollback()
				_logger.exception('Portal RMA create failed for order %s', order.id)
				return self._return_order_form_error(order.id, f'Unable to create return request: {exc}', post)
			created_rmas.append(rma)
			try:
				self._post_rma_chatter(rma, 'create', partner.name, rma.name, rma.reason)
			except Exception:
				_logger.exception('Portal RMA chatter post failed for record %s', rma.id)

		if not created_rmas:
			return self._return_order_form_error(order.id, 'No valid return requests were created.', post)
		if len(created_rmas) == 1:
			return request.redirect(f'/my/return-orders/{created_rmas[0].id}')
		return request.redirect('/my/return-orders')

	@http.route('/my/return-orders/form/<int:order_id>', type='http', auth='user', website=True, methods=['GET'])
	def portal_return_order_form(self, order_id, **kw):
		partner = request.env.user.partner_id
		sale_order = request.env['sale.order'].sudo().browse(order_id)

		if not sale_order.exists() or sale_order.partner_id.commercial_partner_id != partner.commercial_partner_id:
			return request.redirect('/my/return-orders')
		if sale_order.state != 'sale':
			return request.redirect('/my/return-orders')
		if not sale_order.picking_ids.filtered(lambda picking: picking.state == 'done'):
			return request.redirect('/my/return-orders')

		request_types = request.env['rma.request.type'].sudo().search([])
		return request.render(
			'website_quote.portal_return_order_page',
			{
				'sale_order': sale_order,
				'return_types': request_types,
				'return_reasons': False,
				'return_policy': False,
				'rma': False,
			},
		)

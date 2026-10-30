from odoo import http
from odoo.http import request
from odoo.addons.website_sale.controllers.cart import Cart as WebsiteSaleCart


class WebsiteQuoteController(WebsiteSaleCart, http.Controller):

    @http.route(
        '/shop/cart',
        type='http',
        auth='public',
        website=True,
        sitemap=False,
    )
    def cart(self, id=None, access_token=None, revive_method='', **post):
        order = request.cart
        last_quote_order_id = request.session.get('last_quote_order_id')

        if (not order or not order.order_line) and last_quote_order_id:
            quote_order = request.env['sale.order'].sudo().browse(int(last_quote_order_id)).exists()
            if quote_order:
                return request.redirect('/shop/quote/success/%s' % quote_order.id)

        return super().cart(id=id, access_token=access_token, revive_method=revive_method, **post)

    @http.route(
        '/shop/quote',
        type='http',
        auth='public',
        website=True,
        methods=['GET', 'POST'],
        csrf=True,
    )
    def quote_cart(self, **kwargs):
        """Review and edit the current quote using the existing sale.order cart."""
        order = request.cart
        if order and request.httprequest.method == 'POST':
            order = order.sudo()
            client_order_ref = request.params.get('client_order_ref')
            feedback = request.params.get('feedback')
            order.write({'website_quote_feedback': feedback})
            if client_order_ref is not None:
                order.write({'client_order_ref': client_order_ref})

            uploaded = request.httprequest.files.get('document')
            if uploaded and uploaded.filename:
                request.env['ir.attachment'].sudo().create({
                    'name': uploaded.filename,
                    'datas': uploaded.read(),
                    'res_model': 'sale.order',
                    'res_id': order.id,
                    'mimetype': uploaded.mimetype or 'application/octet-stream',
                })

        products = []
        if order:
            for line in order.order_line:
                products.append({
                    'product': line.product_id,
                    'quantity': line.product_uom_qty,
                    'price': line.price_unit,
                })

        disable_checkout = request.env['ir.config_parameter'].sudo().get_param('website_quote.disable_checkout') == 'True'
        return request.render('website_quote.website_quote_cart', {
            'products': products,
            'disable_checkout': disable_checkout,
            'order': order,
        })

    @http.route(
        '/shop/quote/add',
        type='http',
        auth='public',
        website=True,
        methods=['POST'],
        csrf=True,
    )
    def add_to_quote(self, product_id, quantity=1, **kwargs):
        product = request.env['product.product'].sudo().browse(int(product_id))
        if not product.exists() or not product.sale_ok:
            return request.redirect('/shop')

        try:
            quantity = float(quantity)
        except Exception:
            quantity = 1.0

        if quantity <= 0:
            return request.redirect('/shop')

        order = request.cart or request.website._create_cart()
        order.with_context(website_id=request.website.id)._cart_update(
            product_id=product.id,
            add_qty=quantity,
            set_qty=0,
        )
        return request.redirect('/shop/quote')

    @http.route('/shop/quote/update', type='http', auth='public', website=True, methods=['POST'], csrf=True)
    def update_quote_line(self, product_id, quantity=0, **kwargs):
        order = request.cart or request.website._create_cart()
        if order:
            try:
                q = float(quantity)
            except Exception:
                q = 0
            order.with_context(website_id=request.website.id)._cart_update(
                product_id=int(product_id),
                add_qty=0,
                set_qty=q,
            )
        return request.redirect('/shop/quote')

    @http.route('/shop/quote/remove', type='http', auth='public', website=True, methods=['POST'], csrf=True)
    def remove_quote_line(self, product_id, **kwargs):
        order = request.cart or request.website._create_cart()
        if order:
            for line in order.order_line.filtered(lambda l: l.product_id.id == int(product_id)):
                line.unlink()
        return request.redirect('/shop/quote')

    @http.route(
        '/shop/quote/submit',
        type='http',
        auth='public',
        website=True,
        methods=['GET', 'POST'],
        csrf=True,
    )
    def submit_quote(self, **post):
        order = request.cart
        if not order or not order.order_line:
            return request.redirect('/shop')

        for line in order.order_line:
            quantity_key = 'quantity_%s' % line.product_id.id
            quantity = post.get(quantity_key)
            if quantity is not None:
                try:
                    quantity = float(quantity)
                except (TypeError, ValueError):
                    quantity = 0
                if quantity > 0:
                    line.sudo().write({'product_uom_qty': quantity})
                else:
                    line.sudo().unlink()

        order = request.cart
        if not order or not order.order_line:
            return request.redirect('/shop')

        order = order.sudo()
        partner = order.partner_id or request.env.user.partner_id.sudo()
        if request.env.user._is_public():
            email = post.get('email') or (order.partner_id and order.partner_id.email)
            name = post.get('name') or post.get('contact_name') or (order.partner_id and order.partner_id.name)
            if not email or not name:
                return request.redirect('/shop/quote')
            partner = request.env['res.partner'].sudo().search([('email', '=', email)], limit=1)
            if not partner:
                partner = request.env['res.partner'].sudo().create({'name': name, 'email': email})

        feedback = post.get('feedback')

        print('...............post.get feedback or order.website_quote_feedback,........order.',order.website_quote_feedback)
        order.sudo().write({
            'partner_id': partner.id,
            'partner_invoice_id': order.partner_invoice_id.id or partner.id,
            'partner_shipping_id': order.partner_shipping_id.id or partner.id,
            'client_order_ref': post.get('client_order_ref') or order.client_order_ref,
            'website_quote_feedback': post.get('feedback') or order.website_quote_feedback,
            'is_quote_request': True,
            'state': 'draft',
        })
        print('/n/n/n..........website_quote_feedback....',order.website_quote_feedback)
        uploaded = request.httprequest.files.get('document')
        if uploaded and uploaded.filename:
            request.env['ir.attachment'].sudo().create({
                'name': uploaded.filename,
                'datas': uploaded.read(),
                'res_model': 'sale.order',
                'res_id': order.id,
                'mimetype': uploaded.mimetype or 'application/octet-stream',
            })

        template = request.env.ref('website_quote.email_template_quote_request', raise_if_not_found=False).sudo()
        if template:
            template.send_mail(order.id, force_send=True)

        request.session['last_quote_order_id'] = order.id
        request.website.sale_reset()
        return request.redirect('/shop/quote/success/%s' % order.id)

    @http.route(
        '/shop/quote/success/<int:order_id>',
        type='http',
        auth='public',
        website=True,
        methods=['GET'],
    )
    def quote_success(self, order_id, **kwargs):
        order = request.env['sale.order'].sudo().browse(order_id)
        if not order.exists():
            return request.redirect('/shop')
        return request.render('website_quote.website_quote_success', {'order': order})

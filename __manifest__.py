{
    'name': 'Website Quote',
    'version': '19.0.1.0.0',
    'summary': 'Get a quote from website',
    'depends': ['base', 'mail', 'website', 'website_sale', 'sale'],

    'data': [
        'security/ir.model.access.csv',
        'views/res_config_settings_views.xml',
        'views/website_quote_templates.xml',
        'wizard/return_order_wizard_views.xml',
        'views/rma_customer_website.xml',
        'views/rma_customer_views.xml',
        'views/rma_customer_action.xml',
        'views/website_menuitem.xml',

    ],


    'installable': True,
    'application': True,

}

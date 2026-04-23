# -*- coding: utf-8 -*-
{
    'name': 'Google Consent Mode',
    'version': '17.0.1.0.0',
    'summary': 'Google Consent Mode v2 integration for Odoo Website. GDPR-compliant cookie consent with gtag.js support.',
    'description': """
Google Consent Mode v2 for Odoo Website
========================================

Integrate Google Consent Mode v2 directly into your Odoo website without
any additional paid dependencies. Manage all consent parameters from the
Odoo backend UI.

Features:
- Google Consent Mode v2 (all 7 consent parameters)
- Default consent values configurable per website
- Region-based consent defaults (EU/EEA auto-detection)
- Works with Odoo native Cookie Bar
- Works with third-party CMP services
- Multi-website support
- URL Passthrough & Ads Data Redaction options
- No extra paid modules required

Author: Valryx (https://valryx.tech)
Support: valryx.tech@gmail.com
    """,
    'author': 'Valryx',
    'website': 'https://valryx.tech',
    'support': 'valryx.tech@gmail.com',
    'license': 'OPL-1',
    'category': 'Website/Website',
    'depends': ['website', 'mail'],
    'data': [
        'security/ir.model.access.csv',
        'data/default_consent_data.xml',
        'views/website_google_consent_views.xml',
        'views/res_config_settings_views.xml',
        'views/website_templates.xml',
    ],
    'assets': {
        'web.assets_frontend': [
            'website_google_consent_mode/static/src/js/consent_update.js',
        ],
    },
    'images': [
        'static/description/banner.png',
        'static/description/icon.png',
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
    'price': 19.00,
    'currency': 'EUR',
}

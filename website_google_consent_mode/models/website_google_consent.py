# -*- coding: utf-8 -*-
import json as _json
import re
from odoo import api, fields, models, _
from odoo.exceptions import ValidationError

CONSENT_STATES = [
    ('granted', 'Granted'),
    ('denied', 'Denied'),
]

REGION_HELP = (
    "Comma-separated list of ISO 3166-2 region codes. "
    "Example: 'AT,BE,BG,CY,CZ,DE,DK,EE,ES,FI,FR,GB,GR,HR,HU,IE,IT,LT,LU,LV,MT,NL,PL,PT,RO,SE,SI,SK' "
    "for EU/EEA countries. Leave empty to apply to all regions."
)

# FIX 3 — Google Tag ID format: G-XXXXXXXX, GT-XXXXXXXX, AW-XXXXXXXXXX, UA-XXXXXXXX-X
_GTAG_RE = re.compile(
    r'^(G-[A-Z0-9]{4,}|GT-[A-Z0-9]{4,}|AW-[0-9]{4,}|UA-[0-9]+-[0-9]+)$',
    re.IGNORECASE,
)

# FIX 4 — Privacy-safe hard fallback emitted when no records exist
_SAFE_FALLBACK_JSON = _json.dumps({
    "ad_storage": "denied",
    "ad_user_data": "denied",
    "ad_personalization": "denied",
    "analytics_storage": "denied",
    "functionality_storage": "granted",
    "personalization_storage": "denied",
    "security_storage": "granted",
    "wait_for_update": 500,
})


class WebsiteGoogleConsent(models.Model):
    _name = 'website.google.consent'
    _description = 'Google Consent Mode Default Values'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'sequence, id'
    _rec_name = 'name'

    name = fields.Char(
        string='Label',
        required=True,
        help='A descriptive label for this consent configuration (e.g. "EU Default - Denied").',
    )
    sequence = fields.Integer(default=10)
    active = fields.Boolean(default=True)

    website_id = fields.Many2one(
        'website',
        string='Website',
        ondelete='cascade',
        help='Leave empty to apply to all websites.',
    )

    # ── Consent parameters ──────────────────────────────────────────────────
    ad_storage = fields.Selection(
        CONSENT_STATES, string='Ad Storage',
        default='denied',
        required=True,
        help='Enables storage (e.g. cookies) related to advertising.',
    )
    ad_user_data = fields.Selection(
        CONSENT_STATES, string='Ad User Data',
        default='denied',
        required=True,
        help='Consent for sending user data to Google for advertising purposes.',
    )
    ad_personalization = fields.Selection(
        CONSENT_STATES, string='Ad Personalization',
        default='denied',
        required=True,
        help='Consent for personalized advertising.',
    )
    analytics_storage = fields.Selection(
        CONSENT_STATES, string='Analytics Storage',
        default='denied',
        required=True,
        help='Enables storage related to analytics (e.g. visit duration).',
    )
    functionality_storage = fields.Selection(
        CONSENT_STATES, string='Functionality Storage',
        default='granted',
        required=True,
        help='Enables storage that supports website functionality (e.g. language settings).',
    )
    personalization_storage = fields.Selection(
        CONSENT_STATES, string='Personalization Storage',
        default='denied',
        required=True,
        help='Enables storage related to personalization (e.g. video recommendations).',
    )
    security_storage = fields.Selection(
        CONSENT_STATES, string='Security Storage',
        default='granted',
        required=True,
        help='Enables storage related to security (e.g. authentication, fraud prevention).',
    )

    # ── Region & timing ─────────────────────────────────────────────────────
    regions = fields.Char(
        string='Regions',
        help=REGION_HELP,
    )
    wait_for_update = fields.Integer(
        string='Wait for Update (ms)',
        default=500,
        help='Milliseconds to wait for consent signal before sending data to Google.',
    )

    def get_gtag_consent_dict(self):
        """Return a dict suitable for injecting into gtag('consent','default',{...})."""
        self.ensure_one()
        data = {
            'ad_storage': self.ad_storage,
            'ad_user_data': self.ad_user_data,
            'ad_personalization': self.ad_personalization,
            'analytics_storage': self.analytics_storage,
            'functionality_storage': self.functionality_storage,
            'personalization_storage': self.personalization_storage,
            'security_storage': self.security_storage,
        }
        if self.wait_for_update:
            data['wait_for_update'] = self.wait_for_update
        if self.regions:
            region_list = [r.strip() for r in self.regions.split(',') if r.strip()]
            if region_list:
                data['region'] = region_list
        return data

    def get_consent_json(self):
        """Return the consent dict as a safe JSON string for QWeb template injection."""
        self.ensure_one()
        return _json.dumps(self.get_gtag_consent_dict())


class Website(models.Model):
    _inherit = 'website'

    # ── Google Consent Mode settings ────────────────────────────────────────
    google_consent_mode_enabled = fields.Boolean(
        string='Enable Google Consent Mode',
        default=False,
    )
    google_consent_gtag_id = fields.Char(
        string='Google Tag ID (gtag)',
        help='Your Google Tag Measurement ID, e.g. G-XXXXXXXXXX or GT-XXXXXXXX.',
    )
    google_consent_url_passthrough = fields.Boolean(
        string='URL Passthrough',
        default=False,
        help='Pass ad click info (gclid, etc.) through URL parameters when ad_storage is denied.',
    )
    google_consent_ads_data_redaction = fields.Boolean(
        string='Redact Ads Data',
        default=True,
        help='Further redact ads data when ad_storage is denied.',
    )
    google_consent_manager = fields.Selection(
        [
            ('odoo_cookie_bar', 'Odoo Cookie Bar'),
            ('none', 'Third-party CMP / None'),
        ],
        string='Consent Manager',
        default='odoo_cookie_bar',
        help='Select how cookie consent is collected from visitors.',
    )

    # ── FIX 3: Tag ID validation ─────────────────────────────────────────────
    @api.constrains('google_consent_gtag_id', 'google_consent_mode_enabled')
    def _check_gtag_id(self):
        for rec in self:
            if not rec.google_consent_mode_enabled:
                continue
            tag_id = (rec.google_consent_gtag_id or '').strip()
            if not tag_id:
                raise ValidationError(_(
                    "Google Consent Mode is enabled but no Google Tag ID is set.\n"
                    "Please enter your Tag ID (e.g. G-XXXXXXXXXX) in the Website settings."
                ))
            if not _GTAG_RE.match(tag_id):
                raise ValidationError(_(
                    "Invalid Google Tag ID: '%(tag)s'.\n"
                    "Expected format: G-XXXXXXXX, GT-XXXXXXXX, AW-XXXXXXXXXX, or UA-XXXXXXXX-X.",
                    tag=tag_id,
                ))

    # ── FIX 4: Guaranteed fallback — never returns empty ─────────────────────
    def get_active_consent_configs(self):
        """
        Return active consent configs for this website (including global ones).
        Always returns at least the built-in privacy-safe fallback so the QWeb
        template always has something to render — even if the admin deleted all
        records or the data file was not loaded.
        """
        self.ensure_one()
        domain = [
            ('active', '=', True),
            '|',
            ('website_id', '=', self.id),
            ('website_id', '=', False),
        ]
        configs = self.env['website.google.consent'].search(domain, order='sequence, id')
        if configs:
            return configs

        # FIX 4 — No records found: return a transient fallback object so the
        # template never has to handle an empty recordset. We do this by
        # constructing a single new() record (never saved to DB) with safe defaults.
        fallback = self.env['website.google.consent'].new({
            'name': '_fallback',
            'ad_storage': 'denied',
            'ad_user_data': 'denied',
            'ad_personalization': 'denied',
            'analytics_storage': 'denied',
            'functionality_storage': 'granted',
            'personalization_storage': 'denied',
            'security_storage': 'granted',
            'wait_for_update': 500,
        })
        return fallback

    def get_safe_fallback_json(self):
        """Return the module-level privacy-safe fallback JSON string."""
        return _SAFE_FALLBACK_JSON

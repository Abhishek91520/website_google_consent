# -*- coding: utf-8 -*-
from odoo import api, fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    google_consent_mode_enabled = fields.Boolean(
        related='website_id.google_consent_mode_enabled',
        readonly=False,
        string='Enable Google Consent Mode v2',
    )
    google_consent_gtag_id = fields.Char(
        related='website_id.google_consent_gtag_id',
        readonly=False,
        string='Google Tag ID',
    )
    google_consent_url_passthrough = fields.Boolean(
        related='website_id.google_consent_url_passthrough',
        readonly=False,
        string='URL Passthrough',
    )
    google_consent_ads_data_redaction = fields.Boolean(
        related='website_id.google_consent_ads_data_redaction',
        readonly=False,
        string='Redact Ads Data',
    )
    google_consent_manager = fields.Selection(
        related='website_id.google_consent_manager',
        readonly=False,
        string='Consent Manager',
    )

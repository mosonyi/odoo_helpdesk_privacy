# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

{
    'name': 'Helpdesk Privacy',
    'version': '1.0',
    'category': 'Services/Helpdesk',
    'sequence': -100,
    'summary': 'Privacy enabled on Helpdesk',
    'author': 'ZM',
    'maintainer': 'ZM',
    'depends': [
        'helpdesk', 'portal'
    ],
    'description': """
Helpdesk - Privacy Addon
================================

Features:

    - Admin: Rewrite outgoing email's 'From' field from helpdesk internal users private email to the helpdesk's team email address.
    - Admin: Remove the private signature from outgoing email and substitute it with the company name
    - Public portal: Remove 'assinged to' block
    - Public portal: Substitute internal user's email address with the Company's default
    - Public portal: Remove the pictures of the internal users

    """,
    'data': [
        'views/helpdesk_portal_privacy_templates.xml',
        ],
    'demo': [],
    'application': False,
    'license': 'LGPL-3',
    'assets': {}
}

from markupsafe import Markup, escape
from odoo import _, api, fields, models
from pprint import pprint,pformat
from odoo import http
from odoo.osv import expression
from odoo.tools import consteq, plaintext2html
from odoo.addons.helpdesk.controllers import portal
from odoo.addons.portal.controllers import mail
from odoo.addons.mail.models.mail_message import Message
from odoo.addons.mail.models.mail_thread import MailThread
from odoo.addons.web.controllers.main import Binary
from odoo.http import request
import logging


from odoo.exceptions import ValidationError

_logger = logging.getLogger(__name__)

class HelpdeskPrivacy(models.Model):
    _inherit = 'mail.mail'

    def dump(self, obj):
        for attr in dir(obj):
            _logger.info("obj.%s = %r" % (attr, getattr(obj, attr)))

    def send(self, auto_commit=False, raise_exception=False):
        for mail_id in self.ids:
            mail = None
            try:
                mail = self.browse(mail_id)
                if mail.state == 'outgoing' and mail.model == 'helpdesk.ticket':
                    #
                    # Overwrite sender
                    #
                    mail.email_from = mail.reply_to
                res = super(HelpdeskPrivacy, self).send()
                return res
            except Exception as e:
                _logger.exception('failed sending mail')

class HelpdeskPrivacyCustomerPortal(portal.CustomerPortal):

    def dump(self, obj):
        for attr in dir(obj):
            _logger.info("obj.%s = %r" % (attr, getattr(obj, attr)))

    @http.route([
        "/helpdesk/ticket/<int:ticket_id>",
        "/helpdesk/ticket/<int:ticket_id>/<access_token>",
        '/my/ticket/<int:ticket_id>',
        '/my/ticket/<int:ticket_id>/<access_token>'
    ], type='http', auth="public", website=True)
    def tickets_followup(self, ticket_id=None, access_token=None, **kw):
        try:
            ticket_sudo = self._document_check_access('helpdesk.ticket', ticket_id, access_token)
        except (AccessError, MissingError):
            return request.redirect('/my')

        values = self._ticket_get_page_view_values(ticket_sudo, access_token, **kw)
        return request.render("odoo_helpdesk_privacy.tickets_followup", values)

class BinaryPrivacy(Binary):

    def dump(self, obj):
        for attr in dir(obj):
            _logger.info("obj.%s = %r" % (attr, getattr(obj, attr)))

    @http.route(['/web/image',
        '/web/image/<string:xmlid>',
        '/web/image/<string:xmlid>/<string:filename>',
        '/web/image/<string:xmlid>/<int:width>x<int:height>',
        '/web/image/<string:xmlid>/<int:width>x<int:height>/<string:filename>',
        '/web/image/<string:model>/<int:id>/<string:field>',
        '/web/image/<string:model>/<int:id>/<string:field>/<string:filename>',
        '/web/image/<string:model>/<int:id>/<string:field>/<int:width>x<int:height>',
        '/web/image/<string:model>/<int:id>/<string:field>/<int:width>x<int:height>/<string:filename>',
        '/web/image/<int:id>',
        '/web/image/<int:id>/<string:filename>',
        '/web/image/<int:id>/<int:width>x<int:height>',
        '/web/image/<int:id>/<int:width>x<int:height>/<string:filename>',
        '/web/image/<int:id>-<string:unique>',
        '/web/image/<int:id>-<string:unique>/<string:filename>',
        '/web/image/<int:id>-<string:unique>/<int:width>x<int:height>',
        '/web/image/<int:id>-<string:unique>/<int:width>x<int:height>/<string:filename>'], type='http', auth="public")
    def content_image(self, xmlid=None, model='ir.attachment', id=None, field='datas',
                      filename_field='name', unique=None, filename=None, mimetype=None,
                      download=None, width=0, height=0, crop=False, access_token=None,
                      **kwargs):

        if model == 'mail.message' and width and height:
            #
            # TODO: show the company logo if possible
            #
            id = 0
        return super(BinaryPrivacy, self).content_image(xmlid, model, id, field,
                      filename_field, unique, filename, mimetype,
                      download, width, height, crop, access_token,
                      **kwargs)

class MailMessage(Message):
    _inherit = 'mail.message'

    # for attr in dir(author_avatar):
    #     _logger.info("author_avatar.%s = %r" % (attr, getattr(author_avatar, attr)))

    def dump(self, obj):
        for attr in dir(obj):
            _logger.info("obj.%s = %r" % (attr, getattr(obj, attr)))

    def is_internal_user(self, id):
        query = """select * from res_users where partner_id=%(id)s;"""
        self._cr.execute(
            query,
            {
                'id': id
            },
        )
        res = self._cr.fetchone()
        if res:
            return True
        return False


    def _message_format(self, fnames, format_reply=True):
        """ Override the method to add information about a publisher comment
        on each rating messages if requested, and compute a plaintext value of it.
        """
        vals_list = super(MailMessage, self)._message_format(fnames, format_reply=format_reply)

        for vals in vals_list:
            # self.dump(vals.items)
            if 'is_internal' in vals.keys() and not vals['is_internal']:
                if vals['model'] == 'helpdesk.ticket':
                    if self.is_internal_user(vals['author_id'][0]):
                        vals['author_id'] = (1, self.env.company.name)

        return vals_list

    # @api.model
    # def default_get(self, fields):
    #     res = super(MailMessage, self).default_get(fields)
    #     missing_author = 'author_id' in fields and 'author_id' not in res
    #     missing_email_from = 'email_from' in fields and 'email_from' not in res
    #     if missing_author or missing_email_from:
    #         author_id, email_from = self.env['mail.thread']._message_compute_author(res.get('author_id'), res.get('email_from'), raise_exception=False)
    #         if missing_email_from:
    #             res['email_from'] = email_from
    #         if missing_author:
    #             res['author_id'] = author_id
    #     return res

#
# Outgoing emails from admin direct send mail
# Effect: Change signature
#
class PrivacyMailThread(MailThread):
    _inherit = 'mail.thread'

    def dump(self, obj):
        for attr in dir(obj):
            _logger.info("obj.%s = %r" % (attr, getattr(obj, attr)))

    @api.model
    def _notify_prepare_template_context(self, message, msg_vals, model_description=False, mail_auto_delete=True):
        
        res = super(PrivacyMailThread, self)._notify_prepare_template_context(message, msg_vals, model_description, mail_auto_delete)
        model = msg_vals.get('model') if msg_vals else message.model

        if model == 'helpdesk.ticket':
            signature = '<span data-o-mail-quote="1">-- <br data-o-mail-quote="1">%s</span>' % res['company'].name
            signature = Markup(signature)
            res['signature'] = signature
        
        return res
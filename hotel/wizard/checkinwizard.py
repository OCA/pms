import logging
from openerp import models, fields, api
_logger = logging.getLogger(__name__)


class Wizard(models.TransientModel):
    _name = 'checkin.wizard'

    def default_enter_date(self):
        if ('reservation_ids' and 'folio') in self.env.context:
            ids = [item[1] for item in self.env.context.get('reservation_ids')]
            reservations = self.env['hotel.reservation'].browse(ids)
            for res in reservations:
                return res.checkin
        if 'enter_date' in self.env.context:
            return self.env.context['enter_date']
        return False

    def default_exit_date(self):
        if ('reservation_ids' and 'folio') in self.env.context:
            ids = [item[1] for item in self.env.context.get('reservation_ids')]
            reservations = self.env['hotel.reservation'].browse(ids)
            for res in reservations:
                return res.checkout
        if 'exit_date' in self.env.context:
            return self.env.context['exit_date']
        return False

    def default_reservation_id(self):
        if ('reservation_ids' and 'folio') in self.env.context:
            ids = [item[1] for item in self.env.context.get('reservation_ids')]
            reservations = self.env['hotel.reservation'].browse(ids)
            if len(reservations) == 1:
                # return current room line (onlyone in this case)
                return reservations
            for res in reservations:
                # return the first room line with free space for a cardex
                # TODO: add 'done' to res.state condition... Maybe too restrictive right now
                if res.cardex_count < (res.adults + res.children) and \
                        res.state not in ["cancelled"]:
                    return res
        elif 'reservation_id' in self.env.context:
            return self.env['hotel.reservation'].browse(
                self.env.context['reservation_id'])

        _logger.info('default_reservation_id is FALSE')
        return False

    def default_partner_id(self):
        # no partner by default. User must search and choose one
        return False

    def default_cardex_ids(self):
        if ('reservation_ids' and 'folio') in self.env.context:
            ids = [item[1] for item in self.env.context.get('reservation_ids')]
            reservations = self.env['hotel.reservation'].browse(ids)
            for res in reservations:
                return res.cardex_ids

    def default_cardex_ids(self):
        if ('reservation_ids' and 'folio') in self.env.context:
            ids = [item[1] for item in self.env.context.get('reservation_ids')]
            reservations = self.env['hotel.reservation'].browse(ids)
            for res in reservations:
                return res.segmentation_id

    ''' TODO: clean-up
    def default_count_cardex(self):
        if 'reservation_ids' and 'folio' in self.env.context:
            ids = [item[1] for item in self.env.context['reservation_ids']]
            reservations = self.env['hotel.reservation'].browse(ids)
            for res in reservations:
                return res.cardex_count
    '''
    ''' TODO: clean-up
    def default_pending_cardex(self):
        if 'reservation_ids' and 'folio' in self.env.context:
            ids = [item[1] for item in self.env.context['reservation_ids']]
            reservations = self.env['hotel.reservation'].browse(ids)
            for res in reservations:
                return res.adults + res.children - res.cardex_count
    '''
    ''' TODO: clean-up - list of checkins on smart button clean is not used anymore
    def comp_checkin_list_visible(self):
        if 'partner_id' in self.env.context:
            self.list_checkin_cardex = False
        return
    '''
    def comp_checkin_edit(self):
        if 'edit_cardex' in self.env.context:
            return True
        return False

    cardex_ids = fields.Many2many('cardex', 'reservation_id',
                                  default=default_cardex_ids)
    # count_cardex = fields.Integer('Cardex counter',
    #                              default=default_count_cardex)
    # pending_cardex = fields.Integer('Cardex pending',
    #                                 default=default_pending_cardex)
    partner_id = fields.Many2one('res.partner',
                                 default=default_partner_id)
    reservation_id = fields.Many2one('hotel.reservation',
                                     default=default_reservation_id)
    enter_date = fields.Date(default=default_enter_date,
                             required=True)
    exit_date = fields.Date(default=default_exit_date,
                            required=True)

    firstname_cardex = fields.Char('Firstname',
                                   required=True)
    lastname_cardex = fields.Char('Lastname',
                                  required=True)

    email_cardex = fields.Char('E-mail')

    mobile_cardex = fields.Char('Mobile')

    segmentation_id = fields.Many2many(
        related='reservation_id.folio_id.segmentation_ids')


    ''' TODO: clean-up - list of checkins on smart button clean is not used anymore
    list_checkin_cardex = fields.Boolean(compute=comp_checkin_list_visible,
                                         default=True, store=True)
    '''
    # edit_checkin_cardex = fields.Boolean(default=comp_checkin_edit,
    #                                     store=True)

    op_select_partner = fields.Selection([
        ('S', 'Select a partner for checkin'),
        ('C', 'Create a new partner for checkin')
    ], default='S', string='Partner for checkin')
    # checkin mode:
    #   0 - no selection made by the user, so hide the client fields
    #   1 - select a client for update his values and do the checkin
    #   2 - create a new client with the values and do the checkin
    checkin_mode = fields.Integer(default=0)

    @api.multi
    def action_save_check(self):
        # prepare partner values
        if self.op_select_partner == 'S':
            partner_vals = {
                'id': self.partner_id.id,
                'firstname': self.firstname_cardex,
                'lastname': self.lastname_cardex,
                'email': self.email_cardex,
                'mobile': self.mobile_cardex,
            }
            self.partner_id.sudo().write(partner_vals)
        elif self.op_select_partner == 'C':
            partner_vals = {
                'firstname': self.firstname_cardex,
                'lastname': self.lastname_cardex,
                'email': self.email_cardex,
                'mobile': self.mobile_cardex,
            }
            new_partner = self.env['res.partner'].create(partner_vals)
            self.partner_id = self.env['res.partner'].browse(new_partner.id)

        # prepare checkin values
        cardex_val = {
            'partner_id': self.partner_id.id,
            'enter_date': self.enter_date,
            'exit_date': self.exit_date
        }
        record_id = self.env['hotel.reservation'].browse(
            self.reservation_id.id)
        # save the cardex for this reservation
        record_id.write({
            'cardex_ids': [(0, False, cardex_val)],
            'segmentation_id': self.segmentation_id,
        })

        # update the state of the current reservation
        if record_id.cardex_count > 0:
            record_id.state = 'booking'
            record_id.is_checkin = False
            folio = self.env['hotel.folio'].browse(self.reservation_id.folio_id.id)
            folio.checkins_reservations -= 1

    @api.onchange('reservation_id')
    def change_enter_exit_date(self):
        record_id = self.env['hotel.reservation'].browse(
            self.reservation_id.id)

        self.enter_date = record_id.checkin
        self.exit_date = record_id.checkout

        ''' trying to filter the reservations only to pending checkins ...
        if 'reservation_ids' and 'folio' in self.env.context:
            ids = [item[1] for item in self.env.context['reservation_ids']]
            reservations = self.env['hotel.reservation'].browse(ids)
            for res in reservations:
                _logger.info('reservation cardex_count %d', res.cardex_count)

        # return {
            # 'domain': {'reservation_id': [('folio_id','=', self.env.context['folio']), 'count_cardex','=','2']},
            # 'warning': {'title': "Warning", 'message': self.env.context['cardex_count']},
        # }
        '''

    @api.onchange('partner_id')
    def onchange_partner_id(self):
        # update partner fields
        write_vals = {
            'firstname_cardex':  self.partner_id.firstname,
            'lastname_cardex': self.partner_id.lastname,
            'email_cardex': self.partner_id.email,
            'mobile_cardex': self.partner_id.mobile,
        }
        # show the checkin fields if a partner is selected
        if self.op_select_partner == 'S' and self.partner_id.id != False:
            write_vals.update({'checkin_mode': 1})
        self.update(write_vals)

    @api.onchange('op_select_partner')
    def onchange_op_select_partner(self):
        # field one2many return false is record does not exist
        if self.op_select_partner == 'S' and self.partner_id.id:
            self.checkin_mode = 1
        # field one2many return 0 on empty record (nothing typed)
        elif self.op_select_partner == 'C' and self.partner_id.id == 0:
            self.checkin_mode = 2

# Copyright 2017  Alexandre Díaz
# Copyright 2017  Dario Lodeiros
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
import functools
import itertools
import logging
import psycopg2

from odoo import api, fields, models, _
from odoo.osv.expression import get_unaccent_wrapper
from odoo.exceptions import ValidationError, UserError
from odoo.tools import mute_logger
_logger = logging.getLogger(__name__)


class ResPartner(models.Model):
    _inherit = 'res.partner'

    def _compute_reservations_count(self):
        hotel_reservation_obj = self.env['hotel.reservation']
        for record in self:
            record.reservations_count = hotel_reservation_obj.search_count([
                ('partner_id.id', '=', record.id)
            ])

    def _compute_folios_count(self):
        hotel_folio_obj = self.env['hotel.folio']
        for record in self:
            record.folios_count = hotel_folio_obj.search_count([
                ('partner_id.id', '=', record.id)
            ])

    reservations_count = fields.Integer('Reservations',
                                        compute='_compute_reservations_count')
    folios_count = fields.Integer('Folios', compute='_compute_folios_count')
    unconfirmed = fields.Boolean('Unconfirmed', default=True)

    def _get_fk_on(self, table):
        """ return a list of many2one relation with the given table.
            :param table : the name of the sql table to return relations
            :returns a list of tuple 'table name', 'column name'.
        """
        query = """
            SELECT cl1.relname as table, att1.attname as column
            FROM pg_constraint as con, pg_class as cl1, pg_class as cl2, pg_attribute as att1, pg_attribute as att2
            WHERE con.conrelid = cl1.oid
                AND con.confrelid = cl2.oid
                AND array_lower(con.conkey, 1) = 1
                AND con.conkey[1] = att1.attnum
                AND att1.attrelid = cl1.oid
                AND cl2.relname = %s
                AND att2.attname = 'id'
                AND array_lower(con.confkey, 1) = 1
                AND con.confkey[1] = att2.attnum
                AND att2.attrelid = cl2.oid
                AND con.contype = 'f'
        """
        self._cr.execute(query, (table,))
        return self._cr.fetchall()

    @api.multi
    def write(self, vals):
        for i, record in enumerate(self):
            if record.unconfirmed is True:
                partner_dst = self.env['res.partner']._check_duplicated_partner(record)
        res = super(ResPartner, self).write(vals)
        return res

    @api.model
    def name_search(self, name, args=None, operator='ilike', limit=100):
        result = super(ResPartner, self).name_search(name, args=None,
                                                     operator='ilike',
                                                     limit=100)
        if args is None:
            args = []
        if name and operator in ('=', 'ilike', '=ilike', 'like', '=like'):
            self.check_access_rights('read')
            where_query = self._where_calc(args)
            self._apply_ir_rules(where_query, 'read')
            from_clause, where_clause, where_clause_params = where_query.get_sql()
            where_str = where_clause and (" WHERE %s AND " % where_clause) or ' WHERE '

            # search on the name of the contacts and of its company
            search_name = name
            if operator in ('ilike', 'like'):
                search_name = '%%%s%%' % name
            if operator in ('=ilike', '=like'):
                operator = operator[1:]

            unaccent = get_unaccent_wrapper(self.env.cr)

            query = """SELECT id
                         FROM res_partner
                      {where} ({phone} {operator} {percent}
                           OR {mobile} {operator} {percent})
                     ORDER BY {display_name} {operator} {percent} desc,
                              {display_name}
                    """.format(where=where_str,
                               operator=operator,
                               phone=unaccent('phone'),
                               display_name=unaccent('display_name'),
                               mobile=unaccent('mobile'),
                               percent=unaccent('%s'),)

            where_clause_params += [search_name]*3
            if limit:
                query += ' limit %s'
                where_clause_params.append(limit)
            self.env.cr.execute(query, where_clause_params)
            partner_ids = [row[0] for row in self.env.cr.fetchall()]
            if partner_ids:
                result += self.browse(partner_ids).name_get()
        return result

    @api.model
    def _check_duplicated_partner(self, partner):
        duplicated_ids = self.env['res.partner']._get_duplicated_ids(partner)
        if len(duplicated_ids) > 1:
            partners = self.env['res.partner'].browse(duplicated_ids)
            return partner._merge(partners._ids)
        return partner

    def _merge_fields(self):
        duplicated_fields = ['vat']
        return duplicated_fields

    @api.model
    def _get_duplicated_ids(self, partner):
        partner_ids = []
        for field in self.env['res.partner']._merge_fields():
            if partner[field]:
                partner_ids += self.env['res.partner'].search([(field, '=', partner[field])]).ids
        return partner_ids

    def _merge(self, partner_ids, dst_partner=None):
        """ private implementation of merge partner
            :param partner_ids : ids of partner to merge
            :param dst_partner : record of destination res.partner
        """
        partner = self.env['res.partner']
        partner_ids = partner.browse(partner_ids).exists()
        if len(partner_ids) < 2:
            return

        if len(partner_ids) > 3:
            raise UserError(_("For safety reasons, you cannot merge more than 3 contacts together. You can re-open the wizard several times if needed."))

        # check if the list of partners to merge contains child/parent relation
        child_ids = self.env['res.partner']
        for partner_id in partner_ids:
            child_ids |= partner.search([('id', 'child_of', [partner_id.id])]) - partner_id
        if partner_ids & child_ids:
            raise UserError(_("You cannot merge a contact with one of his parent."))

        # remove dst_partner from partners to merge
        if dst_partner and dst_partner in partner_ids:
            src_partners = partner_ids - dst_partner
        else:
            ordered_partners = self._get_ordered_partner(partner_ids.ids)
            dst_partner = ordered_partners[-1]
            src_partners = ordered_partners[:-1]
        _logger.info("dst_partner: %s", dst_partner.id)

        # call sub methods to do the merge
        self._update_foreign_keys(src_partners, dst_partner)
        self._update_reference_fields(src_partners, dst_partner)
        self._update_values(src_partners, dst_partner)

        _logger.info('(uid = %s) merged the partners %r with %s', self._uid, src_partners.ids, dst_partner.id)
        dst_partner.message_post(body='%s %s' % (_("Merged with the following partners:"), ", ".join('%s <%s> (ID %s)' % (p.name, p.email or 'n/a', p.id) for p in src_partners)))

        # delete source partner, since they are merged
        #~ src_partners.update({'active':False})
        src_partners.unlink()
        return dst_partner

    @api.model
    def _update_foreign_keys(self, src_partners, dst_partner):
        """ Update all foreign key from the src_partner to dst_partner. All many2one fields will be updated.
            :param src_partners : merge source res.partner recordset (does not include destination one)
            :param dst_partner : record of destination res.partner
        """
        _logger.debug('_update_foreign_keys for dst_partner: %s for src_partners: %s', dst_partner.id, str(src_partners.ids))

        # find the many2one relation to a partner
        partner = self.env['res.partner']
        relations = self._get_fk_on('res_partner')

        for table, column in relations:
            # get list of columns of current table (exept the current fk column)
            query = "SELECT column_name FROM information_schema.columns WHERE table_name LIKE '%s'" % (table)
            self._cr.execute(query, ())
            columns = []
            for data in self._cr.fetchall():
                if data[0] != column:
                    columns.append(data[0])

            # do the update for the current table/column in SQL
            query_dic = {
                'table': table,
                'column': column,
                'value': columns[0],
            }
            if len(columns) <= 1:
                # unique key treated
                query = """
                    UPDATE "%(table)s" as ___tu
                    SET %(column)s = %%s
                    WHERE
                        %(column)s = %%s AND
                        NOT EXISTS (
                            SELECT 1
                            FROM "%(table)s" as ___tw
                            WHERE
                                %(column)s = %%s AND
                                ___tu.%(value)s = ___tw.%(value)s
                        )""" % query_dic
                for partner in src_partners:
                    self._cr.execute(query, (dst_partner.id, partner.id, dst_partner.id))
            else:
                try:
                    with mute_logger('odoo.sql_db'), self._cr.savepoint():
                        query = 'UPDATE "%(table)s" SET %(column)s = %%s WHERE %(column)s IN %%s' % query_dic
                        self._cr.execute(query, (dst_partner.id, tuple(src_partners.ids),))

                        # handle the recursivity with parent relation
                        if column == partner._parent_name and table == 'res_partner':
                            query = """
                                WITH RECURSIVE cycle(id, parent_id) AS (
                                        SELECT id, parent_id FROM res_partner
                                    UNION
                                        SELECT  cycle.id, res_partner.parent_id
                                        FROM    res_partner, cycle
                                        WHERE   res_partner.id = cycle.parent_id AND
                                                cycle.id != cycle.parent_id
                                )
                                SELECT id FROM cycle WHERE id = parent_id AND id = %s
                            """
                            self._cr.execute(query, (dst_partner.id,))
                            # NOTE JEM : shouldn't we fetch the data ?
                except psycopg2.Error:
                    # updating fails, most likely due to a violated unique constraint
                    # keeping record with nonexistent partner_id is useless, better delete it
                    query = 'DELETE FROM "%(table)s" WHERE "%(column)s" IN %%s' % query_dic
                    self._cr.execute(query, (tuple(src_partners.ids),))

    @api.model
    def _update_reference_fields(self, src_partners, dst_partner):
        """ Update all reference fields from the src_partner to dst_partner.
            :param src_partners : merge source res.partner recordset (does not include destination one)
            :param dst_partner : record of destination res.partner
        """
        _logger.debug('_update_reference_fields for dst_partner: %s for src_partners: %r', dst_partner.id, src_partners.ids)

        def update_records(model, src, field_model='model', field_id='res_id'):
            Model = self.env[model] if model in self.env else None
            if Model is None:
                return
            records = Model.sudo().search([(field_model, '=', 'res.partner'), (field_id, '=', src.id)])
            try:
                with mute_logger('odoo.sql_db'), self._cr.savepoint():
                    return records.sudo().write({field_id: dst_partner.id})
            except psycopg2.Error:
                # updating fails, most likely due to a violated unique constraint
                # keeping record with nonexistent partner_id is useless, better delete it
                return records.sudo().unlink()

        update_records = functools.partial(update_records)

        for partner in src_partners:
            update_records('calendar', src=partner, field_model='model_id.model')
            update_records('ir.attachment', src=partner, field_model='res_model')
            update_records('mail.followers', src=partner, field_model='res_model')
            update_records('mail.message', src=partner)
            update_records('ir.model.data', src=partner)

        records = self.env['ir.model.fields'].search([('ttype', '=', 'reference')])
        for record in records.sudo():
            try:
                Model = self.env[record.model]
                field = Model._fields[record.name]
            except KeyError:
                # unknown model or field => skip
                continue

            if field.compute is not None:
                continue

            for partner in src_partners:
                records_ref = Model.sudo().search([(record.name, '=', 'res.partner,%d' % partner.id)])
                values = {
                    record.name: 'res.partner,%d' % dst_partner.id,
                }
                records_ref.sudo().write(values)

    @api.model
    def _update_values(self, src_partners, dst_partner):
        """ Update values of dst_partner with the ones from the src_partners.
            :param src_partners : recordset of source res.partner
            :param dst_partner : record of destination res.partner
        """
        _logger.debug('_update_values for dst_partner: %s for src_partners: %r', dst_partner.id, src_partners.ids)

        model_fields = dst_partner.fields_get().keys()

        def write_serializer(item):
            if isinstance(item, models.BaseModel):
                return item.id
            else:
                return item
        # get all fields that are not computed or x2many
        values = dict()
        for column in model_fields:
            field = dst_partner._fields[column]
            if field.type not in ('many2many', 'one2many') and field.compute is None:
                for item in itertools.chain(src_partners, [dst_partner]):
                    if item[column]:
                        values[column] = write_serializer(item[column])
        # remove fields that can not be updated (id and parent_id)
        values.pop('id', None)
        parent_id = values.pop('parent_id', None)
        dst_partner.write(values)
        # try to update the parent_id
        if parent_id and parent_id != dst_partner.id:
            try:
                dst_partner.write({'parent_id': parent_id})
            except ValidationError:
                _logger.info('Skip recursive partner hierarchies for parent_id %s of partner: %s', parent_id, dst_partner.id)

    @api.model
    def _get_ordered_partner(self, partner_ids):
        """ Helper : returns a `res.partner` recordset ordered by create_date/active fields
            :param partner_ids : list of partner ids to sort
        """
        return self.env['res.partner'].browse(partner_ids).sorted(
            key=lambda p: (p.active, (p.create_date or '')),
            reverse=True,
        )

    @api.multi
    def _compute_models(self):
        """ Compute the different models needed by the system if you want to exclude some partners. """
        model_mapping = {}
        if self.exclude_contact:
            model_mapping['res.users'] = 'partner_id'
        if 'account.move.line' in self.env and self.exclude_journal_item:
            model_mapping['account.move.line'] = 'partner_id'
        return model_mapping

# -*- coding: utf-8 -*-
###############################################################################
#
#    Module for OpenERP
#    Copyright (C) 2015 Akretion (http://www.akretion.com). All Rights Reserved
#    @author Florian DA COSTA <florian.dacosta@akretion.com>
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
###############################################################################

from openerp.osv import orm, fields
from tools.translate import _
import netsvc

class change_assignment_wizard(orm.TransientModel):
    _name = "change.assignment.wizard"
    _description = "Change Assignment Wizard"

    _columns = {
        'move_line_ids': fields.many2many(
            'move.line.wizard', 'change_assignement_move_wizard_rel',
            'move_id', 'change_assign_id', 'Move List'),
        'move_id': fields.many2one('stock.move', 'Move To Assign'),
        'product_id': fields.many2one('product.product', 'Product'),
        'needed_qty': fields.float('Quantity To Re-assign',
            help="Si la quantité est 0, il y a assez de stock, pas besoin de "
                 "sélectionner de ligne à ré-affecter."),
    }

    def change_move_assignement(self, cr, uid, ids, context=None):
        wf_service = netsvc.LocalService("workflow")
        if context is None:
            context = {}
        move_obj = self.pool['stock.move']
        for wiz in self.browse(cr, uid, ids, context=context):
            for move in wiz.move_line_ids:
                if move.to_reassign:
                    move_obj.cancel_assign(
                        cr, uid, [move.move_id.id], context=context)
            #move_obj.write(cr, uid, [wiz.move_id.id], {'state': 'confirmed', 'location_id': 12}, context=context)
            move_obj.check_assign(cr, uid, [wiz.move_id.id], context=context)

            if wiz.move_id.picking_id:
                wf_service.trg_write(
                    uid, 'stock.picking', wiz.move_id.picking_id.id, cr)
	    return {'type': 'ir.actions.act_window_close'}


class move_line_wizard(orm.TransientModel):
    _name = "move.line.wizard"
    _description = "Assigned Moves"

    _columns = {
        'to_reassign': fields.boolean('Selected'),
        'move_id': fields.many2one('stock.move', 'Targeted Move'),
        'picking_id': fields.many2one('stock.picking', 'Picking'),
        'picking_state': fields.related('picking_id', 'state', type='selection',
            selection=[
                ('draft', 'New'),
                ('auto', 'Waiting Another Operation'),
                ('confirmed', 'Waiting Availability'),
                ('assigned', 'Ready to Process'),
                ('done', 'Done'),
                ('cancel', 'Cancelled'),
                ],string='Picking State'),
        'confirm_date': fields.datetime('Order Date'),
        'date_planned': fields.datetime('Date Planned'),
        'product_qty': fields.float('Quantity'),
        'origin': fields.char('Origin', size=16),
        'partner_id': fields.many2one('res.partner', 'Partner'),
        'sequence': fields.integer('Sequence'),
        'carrier_name': fields.char('Carrier Name', size=32),
        'product_id': fields.many2one('product.product', 'Product'),
    }

    _order = "sequence"


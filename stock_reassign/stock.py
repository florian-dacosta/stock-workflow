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
from openerp.osv.orm import Model


class StockMove(Model):
    _inherit = 'stock.move'

    def get_reserved_moves(self, cr, uid, ids, context=None):
        loc_obj = self.pool['stock.location']
        prod_obj = self.pool['product.product']
        main_wizard_obj = self.pool["change.assignment.wizard"]
        main_move = self.browse(cr, uid, ids, context=context)[0]
        # Try to assign it in case there is enought stock
        main_move.check_assign()
        if main_move.state == 'assigned':
            return True
        picking_id = main_move.picking_id and main_move.picking_id.id or False


        needed_qty = main_move.product_qty

        reserved_move_ids = self.search(
            cr, uid, [('product_id', '=', main_move.product_id.id),
                      ('state', '=', 'assigned'),
                      ('picking_id.state', 'in', ('confirmed', 'assigned')),
                      ('picking_id', '!=', picking_id),
                      ('type', '=', 'out')], context=context)

        move_data = []
        for move in self.browse(cr, uid, reserved_move_ids, context=context):
            picking = move.picking_id or False
            picking_id = picking and picking.id or False
            confirm_date = picking and picking.date or False
            planned_date = picking and picking.min_date or False
            origin = picking and picking.origin or False
            partner_id = picking and picking.partner_id \
                         and picking.partner_id.id or False
            carrier_name = picking and picking.carrier_id \
                           and picking.carrier_id.name or 'No Carrier'
            if needed_qty == move.product_qty 
                    and picking
                    and picking.state == 'confirmed':
                sequence = 0
            elif picking and picking.state == 'confirmed':
                sequence = 1
            elif needed_qty == move.product_qty:
                sequence = 2
            else:
                sequence = 3
            vals = {
                'move_id': move.id,
                'picking_id': picking_id,
                'confirm_date': confirm_date,
                'date_planned': planned_date,
                'origin': origin,
                'partner_id': partner_id,
                'carrier_name': carrier_name,
                'product_id': move.product_id.id,
                'product_qty': move.product_qty,
                'sequence': sequence,
            }
            move_data.append((0, 0, vals))
        main_wiz_vals = {
            'move_id': main_move.id,
            'product_id': main_move.product_id.id,
            'move_line_ids': move_data,
            'needed_qty': needed_qty,
        }
        wiz_id = main_wizard_obj.create(
            cr, uid, main_wiz_vals, context=context)

        # If we let these values in context, the button will try to open these
        # views and generate error since we cant to open a wizard, not a 
        # stock.move view
        if context and context.get('tree_view_ref'):
            del context['tree_view_ref']
        if context and context.get('form_view_ref'):
            del context['form_view_ref']
        value = {
            'name': 'Re-assignement Move View',
            'view_type': 'form',
            'view_mode': 'form,tree',
            'res_model': 'change.assignment.wizard',
            'context': context,
            'type': 'ir.actions.act_window',
            'target': 'new',
            'res_id': wiz_id,
            'nodestroy': True
            }
        return value

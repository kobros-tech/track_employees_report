# -*- coding: utf-8 -*-
###############################################################################
#
#    kobros-tech Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY kobros-tech (<http://www.kobros-tech.com>)
#    Author: kobros-tech (alkobroslymohamed@gmail.com)
#
#    You can modify it under the terms of the GNU AFFERO
#    GENERAL PUBLIC LICENSE (AGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU AFFERO GENERAL PUBLIC LICENSE (AGPL v3) for more details.
#
#    You should have received a copy of the GNU AFFERO GENERAL PUBLIC LICENSE
#    (AGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
###############################################################################
{
    'name': 'Export Project info in Excel',
    'version': '17.0.1.0.0',
    'summary': 'Advanced PDF & XLS reports for Project info.',
    'description': 'Advanced PDF & XLS reports for Project info by',
    'category': 'Project',
    'author': 'Mohamed Alkobrosli',
    'company': 'kobros-tech',
    'maintainer': 'Mohamed Alkobrosli',
    'depends': [
        'project',
    ],
    'website': 'http://www.kobros-tech.com',
    'data': [
        'security/ir.model.access.csv',
        'wizard/select_data_wizard_view.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'export_employee_info_xls/static/src/**/*',
        ],
    },
    'images': ['static/description/banner.png'],
    'license': 'AGPL-3',
}

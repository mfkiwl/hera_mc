#! /usr/bin/env python
# -*- mode: python; coding: utf-8 -*-
# Copyright 2018 the HERA Collaboration
# Licensed under the 2-clause BSD license.

"""script to write M&C records to a CSV file

"""
from __future__ import absolute_import, division, print_function

import sys
import six
from astropy.time import Time, TimeDelta

from hera_mc import mc, cm_utils

valid_tables = {'node_sensors': {'method': 'get_node_sensor_readings',
                                 'filter_column': 'nodeID',
                                 'arg_name': 'node'}}

if __name__ == '__main__':
    parser = mc.get_mc_argument_parser()
    parser.description = """Write M&C records to a CSV file"""
    parser.add_argument('table', help="table to get info from")

    for table, table_dict in six.iteritems(valid_tables):
        arg_name = table_dict['arg_name']
        parser.add_argument('--' + arg_name, help="only include the specified " + arg_name,
                            default=None)

    parser.add_argument('--filename', help="filename to save data to")
    parser.add_argument('--start-date', dest='start_date', help="Start date YYYY/MM/DD", default=None)
    parser.add_argument('--start-time', dest='start_time', help="Start time in HH:MM", default='17:00')
    parser.add_argument('--stop-date', dest='stop_date', help="Stop date YYYY/MM/DD", default=None)
    parser.add_argument('--stop-time', dest='stop_time', help="Stop time in HH:MM", default='7:00')
    parser.add_argument('-l', '--last-period', dest='last_period', default=None,
                        help="Time period from present for data (in minutes).  If present ignores start/stop.")

    args = parser.parse_args()

    if args.last_period:
        stop_time = Time.now()
        start_time = stop_time - TimeDelta(float(args.last_period) / (60.0 * 24.0), format='jd')
    else:
        start_time = cm_utils.get_astropytime(args.start_date, args.start_time)
        stop_time = cm_utils.get_astropytime(args.stop_date, args.stop_time)

    db = mc.connect_to_mc_db(args)
    session = db.sessionmaker()

    method_kwargs = {'starttime': start_time, 'stoptime': stop_time,
                     valid_tables[args.table]['filter_column']: getattr(args, valid_tables[args.table]['arg_name']),
                     'write_to_file': True, 'filename': args.filename}
    getattr(session, valid_tables[args.table]['method'])(**method_kwargs)
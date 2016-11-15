#! /usr/bin/env python
# -*- mode: python; coding: utf-8 -*-
# Copyright 2016 the HERA Collaboration
# Licensed under the 2-clause BSD license.

"""This is meant to hold utility scripts for handling parts and connections

"""
from __future__ import absolute_import, division, print_function

from hera_mc import part_connect, mc, part_handling, geo_location

if __name__ == '__main__':
    handling = part_handling.PartsAndConnections()
    parser = mc.get_mc_argument_parser()
    parser.add_argument('-p', '--hpn', help="Graph data of all elements (per xgraph, ygraph args)", default=None)
    parser.add_argument('-t', '--hptype', help="List the hera part types", action='store_true')
    parser.add_argument('-v', '--verbosity', help="Set verbosity {l, m, h} [m].", default="m")
    parser.add_argument('-c', '--connection', help="Show all connections directly to a part", default=None)
    parser.add_argument('-m', '--mapr', help="Show full hookup chains (see --show_levels)", default=None)
    parser.add_argument('--specify_port', help="Define desired port(s) for hookup [all].", default='all')
    parser.add_argument('--show_levels', help='show power levels if enabled (and able) NOT YET IMPLEMENTED', action='store_true')
    parser.add_argument('--exact_match', help='force exact matches on part numbers, not beginning N char', action='store_true')
    args = parser.parse_args()
    if args.hpn:
        args.hpn = args.hpn.upper()
        part_dict = handling.get_part(args, show_part=True)
    if args.connection:
        args.connection = args.connection.upper()
        connection_dict = handling.get_connection(args, show_connection=True)
    if args.mapr:
        args.mapr = args.mapr.upper()
        hookup_dict = handling.get_hookup(args, show_hookup=True)
    if args.hptype:
        part_type_dict = handling.get_part_types(args, show_hptype=True)

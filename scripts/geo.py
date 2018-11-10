#! /usr/bin/env python
# -*- mode: python; coding: utf-8 -*-
# Copyright 2016 the HERA Collaboration
# Licensed under the 2-clause BSD license.

"""This is meant to hold utility scripts for geo_location (via geo_handling)

"""
from __future__ import absolute_import, division, print_function

import sys

from hera_mc import mc, geo_handling, cm_utils, part_connect

if __name__ == '__main__':
    parser = mc.get_mc_argument_parser()
    parser.add_argument('fg_action', nargs='?', default='active',
                        help="Actions for foreground listing:  a[ctive], i[nstalled], p[osition], c[ofa], s[ince], n[one] (active)")
    parser.add_argument('-p', '--position', help="Position (i.e. station) name for action==position", default=None)
    parser.add_argument('-b', '--background', help="Set background type (layers)",
                        choices=['none', 'installed', 'layers', 'all'], default='layers')
    parser.add_argument('-g', '--graph', help="Graph (plot) station types (False)", action='store_true')
    parser.add_argument('-f', '--file', help="Name of file to write out 'foreground' antennas positions", default=None)
    cm_utils.add_date_time_args(parser)
    parser.add_argument('-x', '--xgraph', help="X-axis of graph. [E]",
                        choices=['N', 'n', 'E', 'e', 'Z', 'z'], default='E')
    parser.add_argument('-y', '--ygraph', help="Y-axis of graph. [N]",
                        choices=['N', 'n', 'E', 'e', 'Z', 'z'], default='N')
    parser.add_argument('-t', '--station-types', help="Station types used for input (csv_list or 'all') Can use types or prefixes.  (default)",
                        dest='station_types', default='default')
    parser.add_argument('--label', choices=['name', 'num', 'ser', 'none'], default='num',
                        help="Label by station_name (name), ant_num (num) serial_num (ser) or none (none) (num)")
    args = parser.parse_args()
    args.fg_action = args.fg_action.lower()
    args.background = args.background.lower()
    args.station_types = args.station_types.lower()
    args.label = args.label.lower()

    allowed_string_station_type_args = ['default', 'all']

    # interpret args
    at_date = cm_utils.get_astropytime(args.date, args.time)
    args.position = cm_utils.listify(args.position)
    if args.station_types not in allowed_string_station_type_args:
        args.station_types = cm_utils.listify(args.station_types)
    if args.label == 'false' or args.label == 'none':
        args.label = False
    xgraph = args.xgraph.upper()
    ygraph = args.ygraph.upper()
    if args.fg_action.startswith('s'):
        cutoff = at_date
        at_date = cm_utils.get_astropytime('now')

    # start session and instances
    db = mc.connect_to_mc_db(args)
    session = db.sessionmaker()
    G = geo_handling.Handling(session)

    # If args.graph is set, apply background
    if args.graph:
        G.set_graph(True)
        if args.background == 'all' or args.background == 'layers':
            G.plot_all_stations()
        if args.background == 'installed' or args.background == 'layers':
            G.plot_station_types(query_date=at_date, station_types_to_use=args.station_types,
                                 xgraph=xgraph, ygraph=ygraph, label=args.label)

    # Process foreground action.
    if args.file is not None:
        G.start_file(args.file)

    if args.fg_action.startswith('a'):
        located = G.get_active_stations(at_date, station_types_to_use=args.station_types)
        G.plot_stations(located, xgraph=xgraph, ygraph=ygraph, label=args.label,
                        marker_color='k', marker_shape='*', marker_size=14)
    elif args.fg_action.startswith('i'):
        G.plot_station_types(query_date=at_date, station_types_to_use=args.station_types,
                             xgraph=xgraph, ygraph=ygraph, label=args.label)
    elif args.fg_action.startswith('p') and args.position is not None:
        located = G.get_location(args.position, at_date)
        G.print_loc_info(located)
        G.plot_stations(located, xgraph=xgraph, ygraph=ygraph, label=args.label,
                        marker_color='k', marker_shape='*', marker_size=14)
    elif args.fg_action.startswith('c'):
        cofa = G.cofa()
        G.print_loc_info(cofa)
        G.plot_stations(cofa, xgraph=xgraph, ygraph=ygraph, label='name',
                        marker_color='k', marker_shape='*', marker_size=14)
    elif args.fg_action.startswith('s'):
        new_antennas = G.get_ants_installed_since(cutoff, args.station_types)
        G.plot_stations(new_antennas, xgraph=xgraph, ygraph=ygraph, label=args.label,
                        marker_color='b', marker_shape='*', marker_size=14)
        print("{} new antennas since {}".format(len(new_antennas), cutoff))
        s = ''
        for na in new_antennas:
            s += na.station_name + ', '
        s = s.strip().strip(',') + '\n'
        print(s)

    if args.graph:
        geo_handling.show_it_now()
    G.close()

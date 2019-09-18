#! /usr/bin/env python
# -*- mode: python; coding: utf-8 -*-
# Copyright 2019 the HERA Collaboration
# Licensed under the 2-clause BSD license.

"""
Allows various views on the antenna hookup, as well as handle the hookup cache file.

"""
from __future__ import absolute_import, division, print_function

import os.path

from hera_mc import cm_hookup, cm_utils, mc

if __name__ == '__main__':
    parser = mc.get_mc_argument_parser()
    parser.add_argument('-p', '--hpn', help="Part number, csv-list or default. (default)", default='default')
    parser.add_argument('-e', '--exact-match', help="Force exact matches on part numbers, not beginning N char.",
                        dest='exact_match', action='store_true')
    parser.add_argument('-f', '--force-new-cache', dest='force_new_cache', help="Force it to write a new hookup cache file.", action='store_true')
    parser.add_argument('-c', '--cache-info', help="Shows information about the hookup cache file.", dest='cache_info', action='store_true')
    parser.add_argument('--force-cache', dest='force_db', help="Force db use (but doesn't rewrite cache)", action='store_false')
    parser.add_argument('--hookup-type', dest='hookup_type', help="Force use of specified hookup type.", default=None)
    parser.add_argument('--pol', help="Define desired pol(s) for hookup. (e, n, all)", default='all')
    parser.add_argument('--all', help="Toggle to show 'all' hookups", action='store_true')
    parser.add_argument('--hookup-cols', help="Specify a subset of parts to show in hookup, comma-delimited no-space list. (all])",
                        dest='hookup_cols', default='all')
    parser.add_argument('--hide-ports', dest='ports', help="Hide ports on hookup.", action='store_false')
    parser.add_argument('--show-revs', dest='revs', help="Show revs on hookup.", action='store_true')
    parser.add_argument('--delete-cache-file', dest='delete_cache_file', help="Deletes the local cache file", action='store_true')
    parser.add_argument('--output-format', dest='output_format', help="table, html, or csv", default='table')
    parser.add_argument('--file', help="output filename, if desired", default=None)
    parser.add_argument('--check', dest='check_data', help="Flag to just check active data for given date.", action='store_true')
    cm_utils.add_date_time_args(parser)

    args = parser.parse_args()

    at_date = cm_utils.get_astropytime(args.date, args.time)

    # Pre-process the args
    args.hookup_cols = cm_utils.listify(args.hookup_cols)
    if args.hpn == 'default':
        args.hpn = cm_utils.default_station_prefixes
    else:
        args.hpn = cm_utils.listify(args.hpn)
    state = 'all' if args.all else 'full'

    # Start session
    db = mc.connect_to_mc_db(args)
    session = db.sessionmaker()
    hookup = cm_hookup.Hookup(session)
    if args.cache_info:
        print(hookup.hookup_cache_file_info())
    elif args.delete_cache_file:
        hookup.delete_cache_file()
    elif args.check_data:
        from hera_mc import cm_dossier
        active = cm_dossier.ActiveDataDossier(session, at_date=at_date)
        active.check()
    else:
        hookup_dict = hookup.get_hookup(hpn=args.hpn, pol=args.pol, at_date=at_date,
                                        exact_match=args.exact_match, force_new_cache=args.force_new_cache,
                                        force_db=args.force_db, hookup_type=args.hookup_type)
        hookup.show_hookup(hookup_dict=hookup_dict, cols_to_show=args.hookup_cols,
                           ports=args.ports, revs=args.revs, state=state,
                           filename=args.file, output_format=args.output_format)

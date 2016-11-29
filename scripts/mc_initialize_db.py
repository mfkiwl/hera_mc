#! /usr/bin/env python
# -*- mode: python; coding: utf-8 -*-
# Copyright 2016 the HERA Collaboration
# Licensed under the 2-clause BSD license.

from __future__ import absolute_import, division, print_function

import hera_mc.mc as mc

parser = mc.get_mc_argument_parser()
args = parser.parse_args()
db = mc.connect_to_mc_db(args)

if not hasattr(db, 'create_tables'):
    raise SystemExit('error: you can only set up a database that\'s '
                     'configured to be in "testing" mode')

db.create_tables()

tables_to_initialize = ['station_meta','parts_paper','part_info','connections']
import initialize_station_meta
import initialize_geo_locations
import initialize_part_numbers
import initialize_connections

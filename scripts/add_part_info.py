#! /usr/bin/env python
# -*- mode: python; coding: utf-8 -*-
# Copyright 2017 the HERA Collaboration
# Licensed under the 2-clause BSD license.

"""
Script to handle adding a comment to the part_info table.
"""

from __future__ import absolute_import, division, print_function

from hera_mc import mc, cm_utils, cm_partconnect, cm_revisions
import six


def query_args(args):
    """
    Gets information from user
    """
    if args.hpn is None:
        args.hpn = six.moves.input('HERA part number:  ')
    args.rev = cm_utils.query_default('rev', args)
    if args.comment is None:
        args.comment = six.moves.input('Comment:  ')
    if args.reference is None:
        args.reference = six.moves.input('reference:  ')
    args.date = cm_utils.query_default('date', args)
    return args


if __name__ == '__main__':
    parser = mc.get_mc_argument_parser()
    parser.add_argument('-p', '--hpn', help="HERA part number", default=None)
    parser.add_argument('-r', '--rev', help="Revision of part", default='last')
    parser.add_argument('-c', '--comment', help="Comment on part", default=None)
    parser.add_argument('-l', '--reference', help="Library filename", default=None)
    parser.add_argument('-q', '--query', help="Set flag if wished to be queried", action='store_true')
    cm_utils.add_date_time_args(parser)
    args = parser.parse_args()

    if args.query:
        args = query_args(args)

    # Pre-process some args
    at_date = cm_utils.get_astropytime(args.date, args.time)
    if type(args.reference) == str and args.reference.lower() == 'none':
        args.reference = None

    db = mc.connect_to_mc_db(args)
    session = db.sessionmaker()
    if args.rev.lower() == 'last':
        args.rev = cm_revisions.get_last_revision(args.hpn, session)[0].rev
        print("Using last revision: {}".format(args.rev))

    # Check for part
    print("Adding info for part {}:{}".format(args.hpn, args.rev))
    cm_partconnect.add_part_info(session, args.hpn, args.rev, at_date, args.comment, args.reference)

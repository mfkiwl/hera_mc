#! /usr/bin/env python
# -*- mode: python; coding: utf-8 -*-
# Copyright 2018 the HERA Collaboration
# Licensed under the 2-clause BSD license.

"""Gather correlator status info and log them into M&C

"""
from __future__ import absolute_import, division, print_function

import sqlalchemy.exc
import sys
import time
import traceback
from astropy.time import Time

from hera_mc import mc

MONITORING_INTERVAL = 60  # seconds

parser = mc.get_mc_argument_parser()
args = parser.parse_args()
db = mc.connect_to_mc_db(args)

# List of commands (methods) to run on each iteration
commands_to_run = ['add_correlator_control_state_from_corrcm',
                   'add_correlator_config_from_corrcm',
                   'add_snap_status_from_corrcm',
                   'add_corr_snap_versions_from_corrcm',
                   'add_antenna_status_from_corrcm']

while True:
    try:
        # Use a single session unless there's an error that isn't fixed by a rollback.
        with db.sessionmaker() as session:
            while True:
                time.sleep(MONITORING_INTERVAL)

                for command in commands_to_run:
                    try:
                        getattr(session, command)()
                    except Exception as e:
                        print('{t} -- error calling command {c}'.format(
                            t=time.asctime(), c=command), file=sys.stderr)
                        traceback.print_exc(file=sys.stderr)
                        traceback_str = traceback.format_exc()
                        session.rollback()
                        try:
                            # try adding an error message to the subsystem_error table
                            session.add_subsystem_error(Time.now,
                                                        'mc_correlator_monitor',
                                                        2, traceback_str)
                        except Exception:
                            # if we can't log error messages to the session, need a new session
                            reraise_context('error logging to subsystem_error '
                                            'table after command "%r"', command)
                        continue
                    try:
                        session.commit()
                    except sqlalchemy.exc.SQLAlchemyError as e:
                        print('{t} -- SQL error committing after command {c}'.format(
                            t=time.asctime(), c=command), file=sys.stderr)
                        traceback.print_exc(file=sys.stderr)
                        traceback_str = traceback.format_exc()
                        session.rollback()
                        try:
                            # try adding an error message to the subsystem_error table
                            session.add_subsystem_error(Time.now,
                                                        'mc_correlator_monitor',
                                                        2, traceback_str)
                        except Exception:
                            # if we can't log error messages to the session, need a new session
                            reraise_context('error logging to subsystem_error '
                                            'table after committing command "%r"',
                                            command)
                        continue
                    except Exception as e:
                        print('{t} -- error committing after command {c}'.format(
                            t=time.asctime(), c=command), file=sys.stderr)
                        traceback.print_exc(file=sys.stderr)
                        traceback_str = traceback.format_exc()
                        try:
                            # First try to roll back the command.
                            session.rollback()
                            try:
                                # try adding an error message to the subsystem_error table
                                session.add_subsystem_error(Time.now,
                                                            'mc_correlator_monitor',
                                                            2, traceback_str)
                            except Exception:
                                # if we can't log error messages to the session, need a new session
                                reraise_context('error logging to subsystem_error '
                                                'table after committing command "%r"',
                                                command)
                            continue
                        except Exception as e2:
                            # If rollback doesn't work, we need a new session.
                            # This should get out of the with statement to create a new session
                            reraise_context('error rolling back after command "%r"', command)
    except Exception:
        # Try to log an error with a new session
        traceback.print_exc(file=sys.stderr)
        with db.sessionmaker() as new_session:
            try:
                # try adding an error message to the subsystem_error table
                session.add_subsystem_error(Time.now,
                                            'mc_correlator_monitor',
                                            2, traceback_str)
            except Exception:
                # if we can't log error messages to the new session we're in real trouble
                reraise_context('error logging to subsystem_error with a new session')
        # restart to get new session
        continue

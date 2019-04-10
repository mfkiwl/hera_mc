# -*- mode: python; coding: utf-8 -*-
# Copyright 2018 the HERA Collaboration
# Licensed under the 2-clause BSD license.

"""Functions to handle various cm table "health" checks.

"""

from __future__ import absolute_import, division, print_function

import warnings
from . import mc, cm_utils
from . import cm_partconn as PC
from . import cm_revisions


def check_for_overlap(interval):
    """
    intervals:  gps_time intervals to test for overlap
                format [[span_1_low, span_1_high], [span_2_low, span_2_high]]
                if the high values are None, they get set to the max value + 100 sec
    """
    maxx = max([x for x in interval[0] + interval[1] if x is not None]) + 100
    for i, ival in enumerate(interval):
        ival[1] = maxx if ival[1] is None else ival[1]
    return interval[0][1] > interval[1][0] and interval[1][1] > interval[0][0]


class Connections:
    def __init__(self, session=None):
        if session is None:  # pragma: no cover
            db = mc.connect_to_mc_db(None)
            self.session = db.sessionmaker()
        else:
            self.session = session
        self.conndict = None

    def ingest_conndb(self):
        """
        conndict - dictionary - conndict[k] = [conn_1, conn_2...]
            Dictionary of connections keyed as:
            upstream_part:rev:output_port:downstream_part:rev:input_port
            with the items being connection classes.
        multiple - set - {key1, ...}
            Set of conndict keys with more than one pair, so there is
            the potential of conflicting times.
        num_connections:
            Integer of the total number of connections in database.
        """
        self.conndict = {}
        self.multiples = set()
        self.num_connections = 0
        for conn in self.session.query(PC.Connections).all():
            self.num_connections += 1
            connection = [conn.upstream_part, conn.up_part_rev, conn.upstream_output_port,
                          conn.downstream_part, conn.down_part_rev, conn.downstream_input_port]
            connection = [x.lower() for x in connection]
            k = ':'.join(connection)
            if k in self.conndict.keys():
                self.multiples.add(k)  # only add to multiples if there is more than one.
            self.conndict.setdefault(k, []).append(conn)

    def check_for_duplicate_connections(self, display_results=False):
        """
        Checks all of the self.multiple keys to see if any of them overlap in time.
        If they do, it is a conflicting duplicate connection.
        if display_results is True, it will print the results.

        Returns the duplicated connections.
        """
        self.ingest_conndb()
        self.duplicates = []
        for k in self.multiples:
            for i in range(len(self.conndict[k])):
                for j in range(i):
                    intervals = [[self.conndict[k][i].start_gpstime, self.conndict[k][i].stop_gpstime],
                                 [self.conndict[k][j].start_gpstime, self.conndict[k][j].stop_gpstime]]
                    if check_for_overlap(intervals):
                        self.duplicates.append([self.conndict[k][i], self.conndict[k][j]])
        if len(self.duplicates):
            s = 's'
            if len(self.duplicates) == 1:
                s = ''
            if display_results:
                print('{} duplicate{} found.'.format(len(self.duplicates), s))
            for dup in self.duplicates:
                i0 = [dup[0].start_gpstime, dup[0].stop_gpstime]
                i1 = [dup[1].start_gpstime, dup[1].stop_gpstime]
                if display_results:
                    print('\t{}  --->  {} {}'.format(dup[0], i0, i1))
        elif display_results:
            print('No duplications found.')
        if display_results:
            print('{} connections checked.'.format(self.num_connections))
        return self.duplicates

    def check_for_existing_connection(self, connection, at_date='now', display_results=False):
        """
        Checks whether the provided connection is already set up for the at_date provided.

        Parameters:
        ------------
        connection:  connection list [upstream, rev, output_port, downstream, rev, input_port]
        at_date:  date for the connection to be made
        """

        at_date = cm_utils.get_astropytime(at_date)
        connection = [x.lower() for x in connection]
        k = ':'.join(connection)
        self.ingest_conndb()
        if k not in self.conndict.keys():
            return False
        for conn in self.conndict[k]:
            t0 = conn.start_gpstime
            t1 = conn.stop_gpstime
            if cm_utils.is_active(at_date, t0, t1):
                if display_results:
                    print('Connection {} is already made for {}  ({} - {})'.format(k, at_date, t0, t1))
                return True
        return False


def check_part_for_overlapping_revisions(hpn, session=None):
    """
    Checks hpn for parts that overlap in time.  They are allowed, but
    may also signal unwanted behavior.

    Returns list of overlapping part revisions

    Parameters:
    ------------
    hpn:  hera part name
    """

    overlap = []
    revisions = cm_revisions.get_all_revisions(hpn, session)
    for i in range(len(revisions)):
        for j in range(i):
            intervals = [[revisions[i].started, cm_utils.get_stopdate(revisions[i].ended)],
                         [revisions[j].started, cm_utils.get_stopdate(revisions[j].ended)]]
            if check_for_overlap(intervals):
                overlap.append([revisions[i], revisions[j]])

    if len(overlap) > 0:
        overlapping_revs_in_single_list = []
        for ol in overlap:
            overlapping_revs_in_single_list.append(ol[0])
            overlapping_revs_in_single_list.append(ol[1])
            s = '{} and {} are overlapping revisions of part {}'.format(
                ol[0].rev, ol[1].rev, hpn)
            warnings.warn(s)
        cm_revisions.show_revisions(overlapping_revs_in_single_list)
    return overlap

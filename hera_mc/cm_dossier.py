#! /usr/bin/env python
# -*- mode: python; coding: utf-8 -*-
# Copyright 2019 the HERA Collaboration
# Licensed under the 2-clause BSD license.

"""
This contains the Entry classes which serves as a "dossier" for part entries,
connections entries, and hookup entries.
"""
from __future__ import absolute_import, division, print_function

import six
import copy

from . import cm_sysdef, cm_utils
from . import cm_partconnect as partconn
from sqlalchemy import func


class PartEntry():
    """
    This class holds all of the information on a given part:rev, including connections,
    part_info, and, if applicable, geo_location.

    It contains the modules to format the dossier for use in the parts display matrix.

    Parameters
    ----------
    hpn : str
        HERA part number - for a single part, not list.  Note: only looks for exact matches.
    rev : str
        HERA revision - this is for a specific revision, not a class of revisions.
    at_date : astropy.Time
        Date after which the part is active.  If inactive, the part will still be included,
        but things like notes, geo etc may exclude on that basis.
    notes_start_date : astropy.Time
        Start date on which to filter notes.  The stop date is at_date above.
    sort_notes_by : str {'part', 'time'}
        Sort notes display by 'part' or 'time'
    """

    col_hdr = {'hpn': 'HERA P/N', 'hpn_rev': 'Rev', 'hptype': 'Part Type',
               'manufacturer_number': 'Mfg #', 'start_date': 'Start', 'stop_date': 'Stop',
               'input_ports': 'Input', 'output_ports': 'Output', 'geo': 'Geo',
               'part_info': 'Note', 'post_date': 'Date', 'lib_file': 'File'}

    def __init__(self, hpn, rev, at_date, notes_start_date, sort_notes_by='part'):
        self.hpn = hpn
        self.rev = rev
        self.entry_key = cm_utils.make_part_key(self.hpn, self.rev)
        self.at_date = at_date
        self.notes_start_date = notes_start_date
        self.part = None  # This is the cm_partconnect.Parts class
        self.part_info = None  # This is a list of cm_partconnect.PartInfo class entries
        self.connections = {'up': None, 'down': None}  # This is the list of connections with part in up/down position
        self.geo = None  # This is the geo_location.GeoLocation class

    def __repr__(self):
        return("{}:{} -- {}".format(self.hpn, self.rev, self.part))

    def get_entry(self, active, full_version=False):
        """
        Gets the part dossier entry.

        Parameters
        ----------
        active : ActiveData class
            Contains the active database entries
        full_version : bool
            Flag to read in the full version, or just use the short version
        """
        self.part = active.parts[self.entry_key]
        self.part.gps2Time()
        if full_version:
            self.get_connections(active=active)
            self.get_part_info(active=active)
            self.get_geo(active=active)

    def get_connections(self, active):
        """
        Retrieves the connection info for the part in self.hpn.

        Parameters
        ----------
        active : ActiveData class
            Contains the active database entries.
        """
        if self.entry_key in active.connections['up'].keys():
            self.connections['up'] = active.connections['up'][self.entry_key]
        if self.entry_key in active.connections['down'].keys():
            self.connections['down'] = active.connections['down'][self.entry_key]

    def get_part_info(self, active):
        """
        Retrieves the part_info for the part in self.hpn.

        Parameters
        ----------
        active : ActiveData class
            Contains the active database entries.
        """
        if self.entry_key in active.info.keys():
            self.part_info = active.info[self.entry_key]

    def get_geo(self, active):
        """
        Retrieves the geographical information for the part in self.hpn

        Parameter
        ---------
        active : ActiveData class
            Contains the active database entries.
        """
        key = cm_utils.make_part_key(self.hpn, None)
        if key in active.geo.keys():
            self.geo = active.geo[key]

    def part_header_titles(self, headers):
        """
        Generates the header titles for the given header names.  The returned header_titles are
        used in the tabulate display.

        Parameters
        ----------
        headers : list
            List of header names.

        Returns
        -------
        list
            The list of the associated header titles.
        """
        header_titles = []
        for h in headers:
            header_titles.append(self.col_hdr[h])
        return header_titles

    def table_entry_row(self, columns):
        """
        Converts the part_dossier column information to a row for the tabulate display.

        Parameters
        ----------
        columns : list
            List of the desired header columns to use.

        Returns
        -------
        list
            A row for the tabulate display.
        """
        tdata = []
            for c in columns:
                try:
                    x = getattr(self, c)
                except AttributeError:
                    try:
                        x = getattr(self.part, c)
                    except AttributeError:
                        x = getattr(self.connections, c)
                if c == 'part_info' and len(x):
                    x = '\n'.join(pi.comment for pi in x)
                elif c == 'geo' and x:
                    x = "{:.1f}E, {:.1f}N, {:.1f}m".format(x.easting, x.northing, x.elevation)
                elif c in ['start_date', 'stop_date']:
                    x = cm_utils.get_time_for_display(x)
                elif isinstance(x, (list, set)):
                    x = ', '.join(x)
                tdata.append(x)
            tdata = [tdata]
        return tdata

    def connection_table_entry_row(self, columns):
        """
        Converts the connections column information to a row for the tabulate display.

        Parameters
        ----------
        columns : list
            List of the desired header columns to use.

        Returns
        -------
        list
            A row for the tabulate display.
        """
        tdata = []
        show_conn_dict = {'Part': self.entry_key}

        for u, d in zip(self.keys_up, self.keys_down):
            if u is None:
                use_upward_connection = False
                for h in ['Upstream', 'uStart', 'uStop', '<uOutput:', ':uInput>']:
                    show_conn_dict[h] = ' '
            else:
                use_upward_connection = True
                c = self.up[u]
                show_conn_dict['Upstream'] = cm_utils.make_part_key(c.upstream_part, c.up_part_rev)
                show_conn_dict['uStart'] = cm_utils.get_time_for_display(c.start_date)
                show_conn_dict['uStop'] = cm_utils.get_time_for_display(c.stop_date)
                show_conn_dict['<uOutput:'] = c.upstream_output_port
                show_conn_dict[':uInput>'] = c.downstream_input_port
            if d is None:
                use_downward_connection = False
                for h in ['Downstream', 'dStart', 'dStop', '<dOutput:', ':dInput>']:
                    show_conn_dict[h] = ' '
            else:
                use_downward_connection = True
                c = self.down[d]
                show_conn_dict['Downstream'] = cm_utils.make_part_key(c.downstream_part, c.down_part_rev)
                show_conn_dict['dStart'] = cm_utils.get_time_for_display(c.start_date)
                show_conn_dict['dStop'] = cm_utils.get_time_for_display(c.stop_date)
                show_conn_dict['<dOutput:'] = c.upstream_output_port
                show_conn_dict[':dInput>'] = c.downstream_input_port
            if use_upward_connection or use_downward_connection:
                r = []
                for h in columns:
                    r.append(show_conn_dict[h])
                tdata.append(r)
        return tdata


class HookupEntry(object):
    """
    This is the structure of the hookup entry.  All are keyed on polarization.

    Parameters
    ----------
    entry_key : str
        Entry key to use for the entry.  Must be None if input_dict is not None.
    sysdef : str
        Name of part type system for the hookup.  Must be None if input_dict is not None.
    input_dict : dict
        Dictionary with seed hookup.  If it is None, entry_key and sysdef must both be provided.
    """
    def __init__(self, entry_key=None, sysdef=None, input_dict=None):
        if input_dict is not None:
            if entry_key is not None:
                raise ValueError('cannot initialize HookupEntry with an '
                                 'entry_key and a dict')
            if sysdef is not None:
                raise ValueError('cannot initialize HookupEntry with an '
                                 'sysdef and a dict')
            self.entry_key = input_dict['entry_key']
            hookup_connections_dict = {}
            for port, conn_list in six.iteritems(input_dict['hookup']):
                new_conn_list = []
                for conn_dict in conn_list:
                    new_conn_list.append(partconn.get_connection_from_dict(conn_dict))
                hookup_connections_dict[port] = new_conn_list
            self.hookup = hookup_connections_dict
            self.fully_connected = input_dict['fully_connected']
            self.hookup_type = input_dict['hookup_type']
            self.columns = input_dict['columns']
            self.timing = input_dict['timing']
            self.sysdef = cm_sysdef.Sysdef(input_dict=input_dict['sysdef'])
        else:
            if entry_key is None:
                raise ValueError('Must initialize HookupEntry with an '
                                 'entry_key and sysdef')
            if sysdef is None:
                raise ValueError('Must initialize HookupEntry with an '
                                 'entry_key and sysdef')
            self.entry_key = entry_key
            self.hookup = {}  # actual hookup connection information
            self.fully_connected = {}  # flag if fully connected
            self.hookup_type = {}  # name of hookup_type
            self.columns = {}  # list with the actual column headers in hookup
            self.timing = {}  # aggregate hookup start and stop
            self.sysdef = sysdef

    def __repr__(self):
        s = "<{}:  {}>\n".format(self.entry_key, self.hookup_type)
        s += "{}\n".format(self.hookup)
        s += "{}\n".format(self.fully_connected)
        s += "{}\n".format(self.timing)
        return s

    def _to_dict(self):
        """
        Convert this object to a dict (so it can be written to json)
        """
        hookup_connections_dict = {}
        for port, conn_list in six.iteritems(self.hookup):
            new_conn_list = []
            for conn in conn_list:
                new_conn_list.append(conn._to_dict())
            hookup_connections_dict[port] = new_conn_list
        return {'entry_key': self.entry_key, 'hookup': hookup_connections_dict,
                'fully_connected': self.fully_connected,
                'hookup_type': self.hookup_type, 'columns': self.columns,
                'timing': self.timing, 'sysdef': self.sysdef._to_dict()}

    def get_hookup_type_and_column_headers(self, port, part_types_found):
        """
        The columns in the hookup contain parts in the hookup chain and the column headers are
        the part types contained in that column.  This returns the headers for the retrieved hookup.

        It just checks which hookup_type the parts are in and keeps however many
        parts are used.

        Parameters
        ----------
        port : str
            Part port to get, of the form 'POL<port', e.g. 'E<ground'
        part_types_found : list
            List of the part types that were found
        """
        self.hookup_type[port] = None
        self.columns[port] = []
        if len(part_types_found) == 0:
            return
        is_this_one = False
        for sp in self.sysdef.checking_order:
            for part_type in part_types_found:
                if part_type not in self.sysdef.full_connection_path[sp]:
                    break
            else:
                is_this_one = sp
                break
        if not is_this_one:
            print('Parts did not conform to any hookup_type')
            return
        else:
            self.hookup_type[port] = is_this_one
            for c in self.sysdef.full_connection_path[is_this_one]:
                if c in part_types_found:
                    self.columns[port].append(c)

    def add_timing_and_fully_connected(self, port):
        """
        Method to add the timing and fully_connected flag for the hookup.

        Parameters
        ----------
        port : str
            Part port to get, of the form 'POL<port', e.g. 'E<ground'
        """
        if self.hookup_type[port] is not None:
            full_hookup_length = len(self.sysdef.full_connection_path[self.hookup_type[port]]) - 1
        else:
            full_hookup_length = -1
        latest_start = 0
        earliest_stop = None
        for c in self.hookup[port]:
            if c.start_gpstime > latest_start:
                latest_start = c.start_gpstime
            if c.stop_gpstime is None:
                pass
            elif earliest_stop is None:
                earliest_stop = c.stop_gpstime
            elif c.stop_gpstime < earliest_stop:
                earliest_stop = c.stop_gpstime
        self.timing[port] = [latest_start, earliest_stop]
        self.fully_connected[port] = len(self.hookup[port]) == full_hookup_length
        self.columns[port].append('start')
        self.columns[port].append('stop')

    def get_part_in_hookup_from_type(self, part_type, include_revs=False, include_ports=False):
        """
        Retrieve the part name for a given part_type from a hookup

        Parameters
        ----------
        part_type : str
            String of valid part type in hookup_dict (e.g. 'snap' or 'feed')
        include_revs : bool
            Flag to include revision number
        include_ports : bool
            Flag to include the associated ports to the part

        Returns
        -------
        dict
            Dictionary keyed on polarization for actual installed part number of
            specified type within hookup as a string per pol
                if include_revs part number is e.g. FDV1:A
                if include_ports they are included as e.g. 'input>FDV:A<terminals'
        """
        parts = {}
        extra_cols = ['start', 'stop']
        for port, names in six.iteritems(self.columns):
            if part_type not in names:
                parts[port] = None
                continue
            iend = 1
            for ec in extra_cols:
                if ec in self.columns[port]:
                    iend += 1
            part_ind = names.index(part_type)
            is_first_one = (part_ind == 0)
            is_last_one = (part_ind == len(names) - iend)
            # Get part number
            if is_last_one:
                part_number = self.hookup[port][part_ind - 1].downstream_part
            else:
                part_number = self.hookup[port][part_ind].upstream_part
            # Get rev
            rev = ''
            if include_revs:
                if is_last_one:
                    rev = ':' + self.hookup[port][part_ind - 1].down_part_rev
                else:
                    rev = ':' + self.hookup[port][part_ind].up_part_rev
            # Get ports
            in_port = ''
            out_port = ''
            if include_ports:
                if is_first_one:
                    out_port = '<' + self.hookup[port][part_ind].upstream_output_port
                elif is_last_one:
                    in_port = self.hookup[port][part_ind - 1].downstream_input_port + '>'
                else:
                    out_port = '<' + self.hookup[port][part_ind].upstream_output_port
                    in_port = self.hookup[port][part_ind - 1].downstream_input_port + '>'
            # Finish
            parts[port] = "{}{}{}{}".format(in_port, part_number, rev, out_port)
        return parts

    def table_entry_row(self, port, columns, part_types, show):
        """
        Produces the hookup table row for given parameters.

        Parameters
        ----------
        port : str
            Polarization type, 'e' or 'n' for HERA (specified in 'cm_sysdef')
        columns : list
            Desired column headers to display
        part_types : dict
            Dictionary containing part_types
        show : dict
            Dictionary containing flags of what components to show.

        Returns
        -------
        list
            List containing the table entry.
        """
        timing = self.timing[port]
        td = ['-'] * len(columns)
        # Get the first N-1 parts
        dip = ''
        for d in self.hookup[port]:
            part_type = part_types[d.upstream_part]
            if part_type in columns:
                new_row_entry = self._build_new_row_entry(
                    dip, d.upstream_part, d.up_part_rev, d.upstream_output_port, show)
                td[columns.index(part_type)] = new_row_entry
            dip = d.downstream_input_port + '> '
        # Get the last part in the hookup
        part_type = part_types[d.downstream_part]
        if part_type in columns:
            new_row_entry = self._build_new_row_entry(
                dip, d.downstream_part, d.down_part_rev, None, show)
            td[columns.index(part_type)] = new_row_entry
        # Add timing
        if 'start' in columns:
            td[columns.index('start')] = timing[0]
        if 'stop' in columns:
            td[columns.index('stop')] = timing[1]
        return td

    def _build_new_row_entry(self, dip, part, rev, port, show):
        """
        Formats the hookup row entry.

        Parameters
        ----------
        dip : str
            Current entry display for the downstream_input_port
        part : str
            Current part name
        rev : str
            Current part revision
        port : str
            Current port name
        show : dict
            Dictionary containing flags of what components to show.

        Returns
        -------
        str
            String containing that row entry.
        """
        new_row_entry = ''
        if show['ports']:
            new_row_entry = dip
        new_row_entry += part
        if show['revs']:
            new_row_entry += ':' + rev
        if port is not None and show['ports']:
            new_row_entry += ' <' + port
        return new_row_entry

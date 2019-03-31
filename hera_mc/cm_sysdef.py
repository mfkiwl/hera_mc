# -*- mode: python; coding: utf-8 -*-
# Copyright 2019 the HERA Collaboration
# Licensed under the 2-clause BSD license.

"""
This module defines all of the system parameters for hookup.  It tries to
contain all of the ad hoc messy part of walking through a signal chain to
this one file.

The two-part "meta" assumption is that:
    a) polarized ports start with one of the polarization characters ('e' or 'n')
    b) non polarized ports don't start with either character.
"""

from __future__ import absolute_import, division, print_function
import six
from argparse import Namespace

port_def = {}
port_def['parts_hera'] = {
    'station': {'up': [[None]], 'down': [['ground']], 'position': 0},
    'antenna': {'up': [['ground']], 'down': [['focus']], 'position': 1},
    'feed': {'up': [['input']], 'down': [['terminals']], 'position': 2},
    'front-end': {'up': [['input']], 'down': [['e'], ['n']], 'position': 3},
    'cable-rfof': {'up': [['ea'], ['na']], 'down': [['eb'], ['nb']], 'position': 4},
    'post-amp': {'up': [['ea'], ['na']], 'down': [['eb'], ['nb']], 'position': 5},
    'snap': {'up': [['e2', 'e6', 'e10'], ['n0', 'n4', 'n8']], 'down': [['rack']], 'position': 6},
    'node': {'up': [['loc1', 'loc2', 'loc3', 'loc4']], 'down': [[None]], 'position': 7}
}
port_def['parts_paper'] = {
    'station': {'up': [[None]], 'down': [['ground']], 'position': 0},
    'antenna': {'up': [['ground']], 'down': [['focus']], 'position': 1},
    'feed': {'up': [['input']], 'down': [['terminals']], 'position': 2},
    'front-end': {'up': [['input']], 'down': [['e'], ['n']], 'position': 3},
    'cable-feed75': {'up': [['ea'], ['na']], 'down': [['eb'], ['nb']], 'position': 4},
    'cable-post-amp(in)': {'up': [['a']], 'down': [['b']], 'position': 5},
    'post-amp': {'up': [['ea'], ['na']], 'down': [['eb'], ['nb']], 'position': 6},
    'cable-post-amp(out)': {'up': [['a']], 'down': [['b']], 'position': 7},
    'cable-receiverator': {'up': [['a']], 'down': [['b']], 'position': 8},
    'cable-container': {'up': [['a']], 'down': [['b']], 'position': 9},
    'f-engine': {'up': [['input']], 'down': [[None]], 'position': 10}
}
port_def['parts_rfi'] = {
    'station': {'up': [[None]], 'down': [['ground']], 'position': 0},
    'antenna': {'up': [['ground']], 'down': [['focus']], 'position': 1},
    'feed': {'up': [['input']], 'down': [['terminals']], 'position': 2},
    'temp-cable': {'up': [['ea'], ['na']], 'down': [['eb'], ['nb']], 'position': 3},
    'snap': {'up': [['e2', 'e6', 'e10'], ['n0', 'n4', 'n8']], 'down': [['rack']], 'position': 4},
    'node': {'up': [['loc1', 'loc2', 'loc3', 'loc4']], 'down': [[None]], 'position': 5}
}
port_def['parts_test'] = {
    'vapor': {'up': [[None]], 'down': [[None]], 'position': 0}
}
pind = {}
this_hookup_type = None


def sys_init(husys, v0):
    y = {}
    for x in husys:
        y[x] = v0
    return y


checking_order = ['parts_hera', 'parts_rfi', 'parts_paper', 'parts_test']
# Initialize the dictionaries
corr_index = sys_init(checking_order, None)
all_pols = sys_init(checking_order, [])
redirect_part_types = sys_init(checking_order, [])
single_pol_labeled_parts = sys_init(checking_order, [])

# Redefine dictionary as needed
corr_index['parts_hera'] = 6
corr_index['parts_paper'] = 10
corr_index['parts_rfi'] = 4
# polarizations should be one character
all_pols['parts_hera'] = ['e', 'n']
all_pols['parts_paper'] = ['e', 'n']
all_pols['parts_rfi'] = ['e', 'n']
redirect_part_types['parts_hera'] = ['node']
single_pol_labeled_parts['parts_paper'] = ['cable-post-amp(in)', 'cable-post-amp(out)', 'cable-receiverator']


full_connection_path = {}
for _x in port_def.keys():
    ordered_path = {}
    for k, v in six.iteritems(port_def[_x]):
        ordered_path[v['position']] = k
    sorted_keys = sorted(list(ordered_path.keys()))
    full_connection_path[_x] = []
    for k in sorted_keys:
        full_connection_path[_x].append(ordered_path[k])


def handle_redirect_part_types(part, port_query):
    """
    This handles the "special cases by feeding a new part list back to hookup."
    """
    from hera_mc import cm_handling, cm_utils
    rptc = cm_handling.Handling()
    conn = rptc.get_part_connection_dossier(part.hpn, part.rev, port=port_query, at_date='now', exact_match=True)
    if part.part_type.lower() == 'node':
        for _k in conn.keys():
            if _k.upper().startswith('N'):
                break
        hpn_list = []
        for _x in conn[_k].keys_up:
            if _x.upper().startswith('SNP'):
                hpn_list.append(cm_utils.split_connection_key(_x)[0])
    return hpn_list


def find_hookup_type(part_type, hookup_type):
    if hookup_type in port_def.keys():
        return hookup_type
    if hookup_type is None:
        for hookup_type in checking_order:
            if part_type in port_def[hookup_type].keys():
                return hookup_type
    raise ValueError("hookup_type {} is not found.".format(hookup_type))


def setup(part, port_query='all', hookup_type=None):
    """
    Given the current part and port_query (which is either 'all', 'e', or 'n')
    this figures out which pols to do.  Basically, given the part and query it
    figures out whether to return ['e*'], ['n*'], or ['e*', 'n*']

    Parameter:
    -----------
    part:  current part dossier
    port_query:  the ports that were requested ('e' or 'n' or 'all')
    hookup_type:  if not None, will use specified hookup_type
                  otherwise it will look through in order
    """
    if hookup_type is None:
        hookup_type = find_hookup_type(part.part_type, None)
    global this_hookup_type, all_pols, pind
    this_hookup_type = hookup_type
    for i, _p in enumerate([x.lower() for x in all_pols[this_hookup_type]]):
        pind[_p] = i

    all_pols_lo = [x.lower() for x in all_pols[this_hookup_type]]
    port_query = port_query.lower()
    port_check_list = all_pols_lo + ['all']
    if port_query not in port_check_list:
        raise ValueError("Invalid port query {}.  Should be in {}".format(port_query, port_check_list))

    # These are for single pol parts that have their polarization as the last letter of the part name
    # This is only for parts_paper parts at this time.  Not a good idea going forward.
    if part.part_type in single_pol_labeled_parts[this_hookup_type]:
        en_part_pol = part.hpn[-1].lower()
        if port_query == 'all' or en_part_pol == port_query:
            return [en_part_pol]
        else:
            return None

    # Sort out all of the ports into 'pol_catalog'
    # It also makes a version of consolidated port_def ports
    pol_catalog = {}
    consolidated_ports = {'up': [], 'down': []}
    for dir in ['up', 'down']:
        pol_catalog[dir] = {'e': [], 'n': [], 'a': [], 'o': []}
        for _c in port_def[this_hookup_type][part.part_type][dir]:
            consolidated_ports[dir] += _c
    connected_ports = {'up': part.connections.input_ports, 'down': part.connections.output_ports}
    for dir in ['up', 'down']:
        for cp in connected_ports[dir]:
            cp = cp.lower()
            if cp not in consolidated_ports[dir]:
                continue
            cp_poldes = 'o' if cp[0] not in all_pols_lo else cp[0]
            if cp_poldes in all_pols_lo:
                pol_catalog[dir]['a'].append(cp)  # p = e + n
            pol_catalog[dir][cp_poldes].append(cp)
    up = pol_catalog['up'][port_query[0]]
    dn = pol_catalog['down'][port_query[0]]

    if (len(up) + len(dn)) == 0:  # The part handles both polarizations
        return all_pols_lo if port_query == 'all' else port_query
    return up if len(up) > len(dn) else dn


# Various dictionaries needed for next_connection below
_D = Namespace(port={'up': 'out', 'down': 'in'},
               this={'up': 'down', 'down': 'up'},
               next={'up': 'up', 'down': 'down'},
               arrow={'up': -1, 'down': 1})


def next_connection(connection_options, current, A, B):
    """
    This checks the options and returns the next connection.
    """
    global this_hookup_type, _D, pind

    # This sets up the parameters to check for the next part/port
    # Also checks for "None and one" to return.
    this_part_type_info = port_def[this_hookup_type][A.part_type]
    next_part_position = this_part_type_info['position'] + _D.arrow[current.direction]
    if next_part_position < 0 or next_part_position > len(full_connection_path[this_hookup_type]) - 1:
        return None
    next_part_type = full_connection_path[this_hookup_type][next_part_position]
    next_part_type_info = port_def[this_hookup_type][next_part_type]
    if len(next_part_type_info[_D.this[current.direction]]) == 2:
        allowed_next_ports = next_part_type_info[_D.this[current.direction]][pind[current.pol]]
    options = []
    # prefix is defined to handle the single_pol_labeled_parts
    prefix_this = A.hpn[-1].lower() if A.part_type in single_pol_labeled_parts[this_hookup_type] else ''
    for i, opc in enumerate(connection_options):
        if B[i].part_type != next_part_type:
            continue
        prefix_next = B[i].hpn[-1].lower() if next_part_type in single_pol_labeled_parts[this_hookup_type] else ''
        if len(connection_options) == 1 or len(next_part_type_info[_D.this[current.direction]]) == 1:
            return opc
        this_port = prefix_this + getattr(opc, '{}stream_{}put_port'.format(_D.this[current.direction], _D.port[_D.this[current.direction]]))
        next_port = prefix_next + getattr(opc, '{}stream_{}put_port'.format(_D.next[current.direction], _D.port[_D.next[current.direction]]))
        if next_port[0] == '@':
            continue
        options.append(Namespace(this=this_port, next=next_port, option=opc))

    # This runs through the Namespace to find the actual part/port
    #    First pass is to check for the specific port-sets that pass
    for opt in options:
        if current.port == opt.this and opt.next in allowed_next_ports:
            return opt.option
    #    Second pass checks for matching the leading polarization character.
    for opt in options:
        if current.pol[0] == opt.this[0] and opt.next in allowed_next_ports:
            return opt.option

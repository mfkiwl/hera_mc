# -*- mode: python; coding: utf-8 -*-
# Copyright 2018 the HERA Collaboration
# Licensed under the 2-clause BSD license.

"""
Methods for handling locating correlator and various system aspects.
"""

from __future__ import absolute_import, division, print_function

import json
import redis
import time
import six
from . import cm_sysutils
from .correlator import DEFAULT_REDIS_ADDRESS


def snap_part_to_host_input(part, rsession=None):
    """
    Given a part string, eg. 'e2>SNPC000008' it will return the putative hostname
    and adc number.  If a redis session is supplied and key available it returns the
    hostname, otherwise it returns the SNAP name.  If None, returns the SNAP name.

    Parameters
    ----------
    part : str
        port>snap part string as returned by cminfo
    rsession : None or redis session
        If redis session and key available it returns the hostname, otherwise SNAP name
        If None, returns the SNAP name

    Returns
    -------
    hostname : str
        hostname as parsed from input 'part' and redis
    adc_num : str
        port ADC number, as parsed from input 'part'
    """
    adc, name = part.split('>')
    adc_num = int(adc[1:]) // 2  # divide by 2 because ADC is in demux 2
    if rsession is None:
        hostname = name
    else:
        _x = rsession.hget('corr:map', 'snap_host')
        if _x is None:
            hostname = name
        else:  # pragma:  no cover
            hostname = json.loads(_x)[name]
    return hostname, adc_num


def cminfo_redis_snap(cminfo, rsession=None):
    """
    Use hera_mc's get_cminfo_correlator method to build a dictionary
    of correlator mappings

    Parameters
    ----------
    cminfo : dict
        Dictionary as returned from get_cminfo_correlator()
    rsession : None or redis session
        Pass through of redis session

    Returns
    -------
    snap_to_ant : dict
        Dictionary mapping the snaps to the antennas
    ant_to_snap : dict
        Dictionary mapping each antenna to its snap
    """
    snap_to_ant = {}
    ant_to_snap = {}
    for antn, ant in enumerate(cminfo['antenna_numbers']):
        name = cminfo['antenna_names'][antn]
        e_pol = None
        n_pol = None
        for pol in cminfo['correlator_inputs'][antn]:
            if pol.lower().startswith('e') and '>' in pol:
                e_pol = pol
            if pol.lower().startswith('n') and '>' in pol:
                n_pol = pol
        ant_to_snap[ant] = {}
        if e_pol is not None:
            snapi_e, channel_e = snap_part_to_host_input(e_pol, rsession=rsession)
            ant_to_snap[ant]['e'] = {'host': snapi_e, 'channel': channel_e}
            snap_to_ant.setdefault(snapi_e, [None] * 6)
            snap_to_ant[snapi_e][channel_e] = name + 'E'
        if n_pol is not None:
            snapi_n, channel_n = snap_part_to_host_input(n_pol, rsession=rsession)
            ant_to_snap[ant]['n'] = {'host': snapi_n, 'channel': channel_n}
            snap_to_ant.setdefault(snapi_n, [None] * 6)
            snap_to_ant[snapi_n][channel_n] = name + 'N'
    return snap_to_ant, ant_to_snap


def cminfo_redis_loc(cminfo):
    """
    Places the positional data into redis for use by the correlator.

    Parameter
    ---------
    cminfo : dict
        Dictionary as returned from get_cminfo_correlator()

    Returns
    -------
    ant_pos : dict
        Dictionary containing the ECEF positions of all of the antennas.
    cofa : dict
        Dictionary containing the lat, lon, alt of the center-of-array
    """
    locations = {}
    locations['antenna_numbers'] = cminfo['antenna_numbers']
    locations['antenna_names'] = cminfo['antenna_names']
    antenna_positions = []
    for _x in cminfo['antenna_positions']:
        antenna_positions.append(list(_x))
    locations['antenna_positions'] = antenna_positions
    locations['antenna_utm_eastings'] = cminfo['antenna_utm_eastings']
    locations['antenna_utm_northings'] = cminfo['antenna_utm_northings']
    locations['cofa'] = {'lat': cminfo['cofa_lat'], 'lon': cminfo['cofa_lon'],
                         'alt': cminfo['cofa_alt']}
    return locations


def set_redis_cminfo(redishost=DEFAULT_REDIS_ADDRESS, session=None):
    """
    Gets the configuration management information and writes to the
    redis database for the correlator.

    Parameters
    ----------
    redishost : None or str
        Hostname for the redis database.  If None uses default
    session : None or hera_mc session
        Session for hera_mc instance.  None uses default
    """
    h = cm_sysutils.Handling(session=session)
    cminfo = h.get_cminfo_correlator()

    # This is retained so that explicitly providing redishost=None has the desired behavior
    if redishost is None:
        redishost = DEFAULT_REDIS_ADDRESS
    redis_pool = redis.ConnectionPool(host=redishost)
    rsession = redis.Redis(connection_pool=redis_pool)

    snap_to_ant, ant_to_snap = cminfo_redis_snap(cminfo, rsession=rsession)
    locations = cminfo_redis_loc(cminfo)
    redhash = {}
    for key, value in six.iteritems(locations):
        redhash[key] = json.dumps(value)
    redhash['snap_to_ant'] = json.dumps(snap_to_ant)
    redhash['ant_to_snap'] = json.dumps(ant_to_snap)
    redhash['update_time'] = time.time()
    redhash['update_time_str'] = time.ctime(redhash['update_time'])
    redhash['cm_version'] = cminfo['cm_version']

    rsession.hmset('corr:map', redhash)

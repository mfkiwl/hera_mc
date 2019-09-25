# -*- mode: python; coding: utf-8 -*-
# Copyright 2016 the HERA Collaboration
# Licensed under the 2-clause BSD license.

"""Testing for `hera_mc.connections`."""

from __future__ import absolute_import, division, print_function

import sys
from contextlib import contextmanager

import six
import pytest
from astropy.time import Time

from hera_mc import cm_partconnect, cm_utils, cm_handling, cm_revisions
from hera_mc.tests import checkWarnings


# define a context manager for checking stdout
# from https://stackoverflow.com/questions/4219717/
#     how-to-assert-output-with-nosetest-unittest-in-python
@contextmanager
def captured_output():
    new_out, new_err = six.StringIO(), six.StringIO()
    old_out, old_err = sys.stdout, sys.stderr
    try:
        sys.stdout, sys.stderr = new_out, new_err
        yield sys.stdout, sys.stderr
    finally:
        sys.stdout, sys.stderr = old_out, old_err


@pytest.fixture(scope='function')
def parts(mcsession):
    test_session = mcsession
    test_part = 'test_part'
    test_rev = 'Q'
    test_hptype = 'antenna'
    start_time = Time('2017-07-01 01:00:00', scale='utc')
    cm_handle = cm_handling.Handling(test_session)

    # Add a test part
    part = cm_partconnect.Parts()
    part.hpn = test_part
    part.hpn_rev = test_rev
    part.hptype = test_hptype
    part.manufacture_number = 'XYZ'
    part.start_gpstime = start_time.gps
    test_session.add(part)
    test_session.commit()

    class DataHolder(object):
        def __init__(self, test_session, test_part, test_rev, test_hptype,
                     start_time, cm_handle):
            self.test_session = test_session
            self.test_part = test_part
            self.test_rev = test_rev
            self.test_hptype = test_hptype
            self.start_time = start_time
            self.cm_handle = cm_handle

    parts = DataHolder(test_session, test_part, test_rev, test_hptype,
                       start_time, cm_handle)

    # yields the data we need but will continue to the del call after tests
    yield parts

    # some post-test object cleanup
    del(parts)

    return


def test_update_new(parts):
    ntp = 'new_test_part'
    data = [[ntp, 'X', 'hpn', ntp],
            [ntp, 'X', 'hpn_rev', 'X'],
            [ntp, 'X', 'hptype', 'antenna'],
            [ntp, 'X', 'start_gpstime', 1172530000]]
    cm_partconnect.update_part(parts.test_session, data)
    located = parts.cm_handle.get_part_dossier(hpn=[ntp], rev='X',
                                               at_date='now', exact_match=True)
    prkey = list(located.keys())[0]
    assert str(located[prkey]).startswith('NEW_TEST_PART:X')
    assert len(list(located.keys())) == 1
    assert located[list(located.keys())[0]].part.hpn == ntp


def test_find_part_type(parts):
    pt = parts.cm_handle.get_part_type_for(parts.test_part)
    assert pt == parts.test_hptype


def test_update_part(parts):
    data = [[parts.test_part, parts.test_rev, 'not_an_attrib', 'Z']]
    with captured_output() as (out, err):
        cm_partconnect.update_part(parts.test_session, data)
    assert 'does not exist as a field' in out.getvalue().strip()
    data = [[parts.test_part, parts.test_rev, 'hpn_rev', 'Z']]
    cm_partconnect.update_part(parts.test_session, data)
    dtq = Time('2017-07-01 01:00:00', scale='utc')
    located = parts.cm_handle.get_part_dossier(
        hpn=[parts.test_part], rev='Z', at_date=dtq, exact_match=True)
    assert len(list(located.keys())) == 1
    assert located[list(located.keys())[0]].part.hpn_rev == 'Z'


def test_format_and_check_update_part_request(parts):
    request = 'test_part:Q:hpn_rev:A'
    x = cm_partconnect.format_and_check_update_part_request(request)
    assert list(x.keys())[0] == 'test_part:Q'
    pytest.raises(ValueError,
                  cm_partconnect.format_and_check_update_part_request,
                  'test_part:hpn_rev:A')
    request = 'test_part:Q:hpn_rev:A,test_part:mfg:xxx,nope,another:one'
    x = cm_partconnect.format_and_check_update_part_request(request)
    assert x['test_part:Q'][2][3] == 'one'


def test_part_dossier(parts):
    located = parts.cm_handle.get_part_dossier(
        hpn=None, rev=None, at_date='now', sort_notes_by='part',
        exact_match=True)
    assert list(located.keys())[0] == '__Sys__'
    located = parts.cm_handle.get_part_dossier(
        hpn=None, rev=None, at_date='now', sort_notes_by='post',
        exact_match=True)
    with captured_output() as (out, err):
        parts.cm_handle.show_parts(located, notes_only=True)
    assert 'System:A' in out.getvalue().strip()


def test_show_parts(parts):
    cm_partconnect.add_part_info(
        parts.test_session, parts.test_part, parts.test_rev, parts.start_time,
        'Testing', 'library_file')
    located = parts.cm_handle.get_part_dossier(
        hpn=[parts.test_part], rev=parts.test_rev, at_date='now',
        exact_match=True)
    with captured_output() as (out, err):
        parts.cm_handle.show_parts(located)
    assert ('TEST_PART  | Q     | antenna     |         | 2017-07-01 01:00:37'
            in out.getvalue().strip())
    with captured_output() as (out, err):
        parts.cm_handle.show_parts(located, notes_only=True)
    assert 'library_file' in out.getvalue().strip()
    with captured_output() as (out, err):
        parts.cm_handle.show_parts({})
    assert 'Part not found' in out.getvalue().strip()
    located = parts.cm_handle.get_part_dossier(
        hpn=['A0'], rev=['H'], at_date='now', exact_match=True)
    with captured_output() as (out, err):
        parts.cm_handle.show_parts(located, notes_only=True)
    assert 'Comment 2' in out.getvalue().strip()
    located = parts.cm_handle.get_part_dossier(
        hpn=['HH0'], rev=['A'], at_date='now', exact_match=True)
    with captured_output() as (out, err):
        parts.cm_handle.show_parts(located)
    assert '540901.6E, 6601070.7N, 1052.6m' in out.getvalue().strip()


def test_part_info(parts):
    cm_partconnect.add_part_info(
        parts.test_session, parts.test_part, parts.test_rev,
        Time('2017-07-01 01:00:00'), 'Testing', 'library_file')
    located = parts.cm_handle.get_part_dossier(
        hpn=[parts.test_part], rev=parts.test_rev, at_date='now',
        exact_match=True)
    assert located[list(located.keys())[0]].part_info[0].comment == 'Testing'
    test_info = cm_partconnect.PartInfo()
    test_info.info(hpn='A', hpn_rev='B', posting_gpstime=1172530000,
                   comment='Hey Hey!')
    with captured_output() as (out, err):
        print(test_info)
    assert 'heraPartNumber id = A:B' in out.getvalue().strip()
    test_info.gps2Time()
    assert int(test_info.posting_date.gps) == 1172530000


def test_add_new_parts(parts):
    a_time = Time('2017-07-01 01:00:00', scale='utc')
    data = [[parts.test_part, parts.test_rev, parts.test_hptype, 'xxx']]
    with captured_output() as (out, err):
        cm_partconnect.add_new_parts(parts.test_session, data, a_time, True)
    assert "No action." in out.getvalue().strip()

    cm_partconnect.stop_existing_parts(parts.test_session, data, a_time, False)
    with captured_output() as (out, err):
        cm_partconnect.add_new_parts(parts.test_session, data, a_time, False)
    assert "No action." in out.getvalue().strip()
    with captured_output() as (out, err):
        cm_partconnect.add_new_parts(parts.test_session, data, a_time, True)
    assert "Restarting part test_part:q" in out.getvalue().strip()

    data = [['part_X', 'X', 'station', 'mfg_X']]
    p = cm_partconnect.Parts()
    p.part(test_attribute='test')
    assert p.test_attribute == 'test'
    cm_partconnect.add_new_parts(parts.test_session, data, a_time, True)
    located = parts.cm_handle.get_part_dossier(
        hpn=['part_X'], rev='X', at_date=a_time, exact_match=True)
    assert len(list(located.keys())) == 1
    assert located[list(located.keys())[0]].part.hpn == 'part_X'


def test_stop_parts(parts):
    hpnr = [['test_part', 'Q']]
    at_date = Time('2017-12-01 01:00:00', scale='utc')
    cm_partconnect.stop_existing_parts(parts.test_session, hpnr, at_date,
                                       allow_override=False)
    p = parts.cm_handle.get_part_from_hpnrev(hpnr[0][0], hpnr[0][1])
    assert p.stop_gpstime == 1196125218
    with captured_output() as (out, err):
        cm_partconnect.stop_existing_parts(parts.test_session, hpnr, at_date,
                                           allow_override=False)
    assert "Override not enabled.  No action." in out.getvalue().strip()
    with captured_output() as (out, err):
        cm_partconnect.stop_existing_parts(parts.test_session, hpnr, at_date,
                                           allow_override=True)
    assert "Override enabled.   New value 1196125218" in out.getvalue().strip()
    hpnr = [['no_part', 'Q']]
    with captured_output() as (out, err):
        cm_partconnect.stop_existing_parts(parts.test_session, hpnr, at_date,
                                           allow_override=False)
    assert "no_part:Q is not found, so can't stop it." in out.getvalue().strip()


def test_cm_version(parts):
    parts.cm_handle.add_cm_version(cm_utils.get_astropytime('now'),
                                   'Test-git-hash')
    gh = parts.cm_handle.get_cm_version()
    assert gh == 'Test-git-hash'


def test_get_revisions_of_type(parts):
    at_date = None
    rev_types = ['LAST', 'ACTIVE', 'ALL', 'A']
    for rq in rev_types:
        revision = cm_revisions.get_revisions_of_type(
            'HH0', rq, at_date, parts.test_session)
        assert revision[0].rev == 'A'
        revision = cm_revisions.get_revisions_of_type(
            None, rq, at_date, parts.test_session)
        assert len(revision) == 0
    revision = cm_revisions.get_revisions_of_type(
        'TEST_FEED', 'LAST', 'now', parts.test_session)
    assert revision[0].rev == 'Z'
    revision = cm_revisions.get_revisions_of_type(
        None, 'ACTIVE', 'now', parts.test_session)
    with captured_output() as (out, err):
        cm_revisions.show_revisions(revision)
    assert 'No revisions found' in out.getvalue().strip()
    revision = cm_revisions.get_revisions_of_type(
        'HH23', 'ACTIVE', 'now', parts.test_session)
    with captured_output() as (out, err):
        cm_revisions.show_revisions(revision)
    assert '1096509616.0' in out.getvalue().strip()
    assert revision[0].hpn == 'HH23'


def test_match_listify(parts):
    testing = [['hpn', 'rev'], [['hpn1', 'hpn2', 'hpn3'], 'rev'],
               [['hpn1', 'hpn2'], ['rev1', 'rev2']]]
    for testit in testing:
        h, r = cm_utils.match_listify(testit[0], testit[1])
        assert len(h) == len(r)
    pytest.raises(ValueError, cm_utils.match_listify, ['hpn'], ['A', 'B'])
    x = cm_utils.listify(1)
    assert x[0] == 1


def test_get_part_types(parts):
    at_date = cm_utils.get_astropytime('now')
    a = parts.cm_handle.get_part_types('all', at_date)
    assert 'terminals' in a['feed']['output_ports']
    with captured_output() as (out, err):
        parts.cm_handle.show_part_types()
    assert 'A, B, Q, R, Z' in out.getvalue().strip()


def test_check_overlapping(parts):
    from .. import cm_health
    c = cm_health.check_part_for_overlapping_revisions(
        parts.test_part, parts.test_session)
    assert len(c) == 0
    # Add a test part
    part = cm_partconnect.Parts()
    part.hpn = parts.test_part
    part.hpn_rev = 'B'
    part.hptype = parts.test_hptype
    part.manufacture_number = 'XYZ'
    part.start_gpstime = parts.start_time.gps
    parts.test_session.add(part)
    parts.test_session.commit()
    c = checkWarnings(
        cm_health.check_part_for_overlapping_revisions,
        func_args=[parts.test_part, parts.test_session],
        message='Q and B are overlapping revisions of part test_part')
    assert len(c) == 1


def test_datetime(parts):
    dt = cm_utils.get_astropytime('2017-01-01', 0.0)
    gps_direct = int(Time('2017-01-01 00:00:00', scale='utc').gps)
    assert int(dt.gps) == gps_direct

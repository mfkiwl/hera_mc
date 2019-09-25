# -*- mode: python; coding: utf-8 -*-
# Copyright 2016 the HERA Collaboration
# Licensed under the 2-clause BSD license.

"""Testing for `hera_mc.cm_transfer`."""

from __future__ import absolute_import, division, print_function

import argparse
import sys
import subprocess
import os

import pytest

import hera_mc
from hera_mc import cm_utils, mc


def test_log():
    from argparse import Namespace
    a = Namespace(test=True, val=0)
    cm_utils.log('testing', args=a)


def test_various():
    a, b, c, d = cm_utils.split_connection_key('a:b:c:d')
    assert c[0] == 'c'
    args = argparse.Namespace(a='def_test', unittesting='')
    x = cm_utils.query_default(a, args)
    assert x == 'def_test'
    args = argparse.Namespace(a='def_test', unittesting='none')
    x = cm_utils.query_default(a, args)
    assert x is None
    args = argparse.Namespace(a='def_test', unittesting='false')
    x = cm_utils.query_default(a, args)
    assert not x
    args = argparse.Namespace(a='def_test', unittesting='true')
    x = cm_utils.query_default(a, args)
    assert x
    args = argparse.Namespace(a='def_test', unittesting='unittest')
    x = cm_utils.query_default(a, args)
    assert x == 'unittest'


def test_stringify_listify():
    x = cm_utils.stringify(None)
    assert x is None
    x = cm_utils.stringify('Test')
    assert x == 'Test'
    x = cm_utils.stringify(['a', 'b'])
    assert x == 'a,b'
    x = cm_utils.stringify(0)
    assert x == '0'
    x = cm_utils.listify(None)
    assert x is None
    x = cm_utils.listify('Test')
    assert x[0] == 'Test'
    x = cm_utils.listify('a,b')
    assert x[0] == 'a'
    x = cm_utils.listify(['a', 'b'])
    assert x[0] == 'a'


def test_verbosity():
    sys.argv = ['test', '-v', '0']
    p = argparse.ArgumentParser()
    cm_utils.add_verbosity_args(p)
    args = p.parse_args()
    x = cm_utils.parse_verbosity(args.verbosity)
    assert x == 0
    x = cm_utils.parse_verbosity(None)
    assert x == 1
    x = cm_utils.parse_verbosity('vv')
    assert x == 3
    pytest.raises(ValueError, cm_utils.parse_verbosity, 'x')


def test_datetime():
    from astropy.time import Time
    sys.argv = ['test']
    p = argparse.ArgumentParser()
    cm_utils.add_date_time_args(p)
    args = p.parse_args()
    assert args.date == 'now'
    assert args.time == 0.0
    import datetime
    tout = cm_utils.get_astropytime(datetime.datetime.now())
    assert type(tout) == Time
    tout = cm_utils.get_astropytime(2400001.0)
    assert type(tout) == Time
    pytest.raises(ValueError, cm_utils.get_astropytime, 0.0)
    tout = cm_utils.get_astropytime('none')
    assert tout is None
    tout = cm_utils.get_astropytime('2018/1/1', '0.0')
    assert type(tout) == Time
    pytest.raises(ValueError, cm_utils.get_astropytime, '18/1/1')
    tout = cm_utils.get_astropytime('2018/1/1', '12:30:00')
    assert type(tout) == Time
    pytest.raises(ValueError, cm_utils.get_astropytime, '2018/1/1', '0:0:0:0')
    pytest.raises(ValueError, cm_utils.get_astropytime, '2018/1/1', 'x')


def test_put_keys_in_numerical_order():
    x = cm_utils.put_keys_in_numerical_order(['HH1', 'HH0:A'])
    assert x[0] == 'HH0:A'


def test_get_cm_repo_git_hash():
    cm_hash = cm_utils.get_cm_repo_git_hash(cm_csv_path=mc.test_data_path)

    git_hash = subprocess.check_output(['git', '-C', '.', 'rev-parse', 'HEAD'],
                                       stderr=subprocess.STDOUT).strip()

    assert cm_hash, git_hash

    example_config_path = os.path.join(os.path.dirname(hera_mc.__path__[0]),
                                       'ci', 'example_config.json')
    pytest.raises(ValueError, cm_utils.get_cm_repo_git_hash,
                  mc_config_path=example_config_path)

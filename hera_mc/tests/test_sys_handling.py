# -*- mode: python; coding: utf-8 -*-
# Copyright 2017 the HERA Collaboration
# Licensed under the 2-clause BSD license.

"""Testing for `hera_mc.geo_location and geo_handling`.


"""

from __future__ import absolute_import, division, print_function

import unittest
import os.path
import subprocess
import numpy as np
from hera_mc import geo_location, sys_handling, mc, cm_transfer, part_connect
from hera_mc import cm_hookup, cm_utils, cm_revisions
from hera_mc.tests import TestHERAMC
from astropy.time import Time, TimeDelta


class TestSys(TestHERAMC):

    def setUp(self):
        super(TestSys, self).setUp()
        self.h = sys_handling.Handling(self.test_session)

    def test_ever_fully_connected(self):
        now_list = self.h.get_all_fully_connected_at_date(at_date='now')
        self.assertEqual(len(now_list), 1)

    def test_publish_summary(self):
        msg = self.h.publish_summary()
        self.assertEqual(msg, 'Not on "main"')

    def test_other_hookup(self):
        at_date = cm_utils.get_astropytime('2017-07-03')
        H = cm_hookup.Hookup(at_date=at_date, session=self.test_session)
        H.reset_memory_cache(None)
        self.assertEqual(H.cached_hookup_dict, None)
        hu = H.get_hookup(['A23'], 'H', 'pol', exact_match=True, force_new=True)
        H.reset_memory_cache(hu)
        self.assertEqual(H.cached_hookup_dict['A23:H'].hookup['e'][0].upstream_part, 'HH23')

    def test_hookup_cache_file_info(self):
        H = cm_hookup.Hookup(at_date='now', session=self.test_session)
        s = H.hookup_cache_file_info()

    def test_correlator_info(self):
        corr_dict = self.h.get_cminfo_correlator()
        ant_names = corr_dict['antenna_names']
        self.assertEqual(len(ant_names), 1)

        corr_inputs = corr_dict['correlator_inputs']

        stn_types = corr_dict['station_types']

        index = np.where(np.array(ant_names) == 'HH0')[0]
        self.assertEqual(len(index), 1)
        index = index[0]

        self.assertEqual(stn_types[index], 'herahexw')

        self.assertEqual(corr_inputs[index], ('DF8B2', 'DF8B1'))

        self.assertEqual([int(name.split('HH')[1]) for name in ant_names],
                         corr_dict['antenna_numbers'])

        self.assertEqual(set(corr_dict['antenna_numbers']),
                         set([0]))

        self.assertTrue(corr_dict['cm_version'] is not None)

        # cm_version should be the same as the git hash of m&c for the test data
        mc_dir = os.path.dirname(os.path.realpath(__file__))
        mc_git_hash = subprocess.check_output(['git', '-C', mc_dir, 'rev-parse', 'HEAD'],
                                              stderr=subprocess.STDOUT).strip()
        self.assertEqual(corr_dict['cm_version'], mc_git_hash)

        expected_keys = ['antenna_numbers', 'antenna_names', 'station_types',
                         'correlator_inputs', 'antenna_utm_datum_vals',
                         'antenna_utm_tiles', 'antenna_utm_eastings',
                         'antenna_utm_northings', 'antenna_positions',
                         'cm_version', 'cofa_lat', 'cofa_lon', 'cofa_alt']
        self.assertEqual(set(corr_dict.keys()), set(expected_keys))

        cofa = self.h.cofa()[0]
        self.assertEqual(cofa.lat, corr_dict['cofa_lat'])
        self.assertEqual(cofa.lon, corr_dict['cofa_lon'])
        self.assertEqual(cofa.elevation, corr_dict['cofa_alt'])

    def test_dubitable(self):
        at_date = cm_utils.get_astropytime('2017-01-01')
        part_connect.update_dubitable(self.test_session, at_date.gps, ['1', '2', '3'])
        a = self.h.get_dubitable_list()
        alist = a.split(",")
        self.assertEqual(len(alist), 3)
        a = self.h.get_dubitable_list(return_full=True)
        self.assertEqual(len(a[2]), 3)

    def test_get_pam_from_hookup(self):
        at_date = cm_utils.get_astropytime('2017-07-03')
        H = cm_hookup.Hookup(at_date, self.test_session)
        stn = 'HH23'
        hud = H.get_hookup([stn], exact_match=True)
        pams = hud[hud.keys()[0]].get_part_info('post-amp')
        self.assertEqual(len(pams), 2)
        self.assertEqual(pams['e'], 'PAM75123')  # the actual pam number (the thing written on the case)

    def test_get_pam_info(self):
        h = sys_handling.Handling(self.test_session)
        pams = h.get_part_info('HH23', '2017-07-03', 'post-amp')
        self.assertEqual(len(pams), 1)
        self.assertEqual(pams['HH23:A']['e'], 'PAM75123')  # the actual pam number (the thing written on the case)

    def test_system_comments(self):
        comments = self.h.system_comments()
        self.assertEqual(comments[0], 'N')


if __name__ == '__main__':
    unittest.main()

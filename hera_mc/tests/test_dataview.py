# -*- mode: python; coding: utf-8 -*-
# Copyright 2017 the HERA Collaboration
# Licensed under the 2-clause BSD license.

"""Testing for `hera_mc.cm_dataview`.


"""

from __future__ import absolute_import, division, print_function

import unittest

from astropy.time import Time, TimeDelta
import os
import os.path

from hera_mc import mc, cm_utils, cm_dataview
from hera_mc.tests import TestHERAMC


class TestParts(TestHERAMC):

    def setUp(self):
        super(TestParts, self).setUp()

        self.start_time = Time('2017-07-01 01:00:00', scale='utc')
        self.now = cm_utils._get_astropytime('now')

    def test_dbread_write_file(self):
        output_options = ['flag', 'corr']
        filename = ['testflag.txt', 'testcorr.txt']
        parts_list = ['HH0']
        fc_map = cm_dataview.read_db(parts_list, self.start_time, self.now, dt=1.0,
                                     full_req=['station', 'f_engine'], lsession=self.test_session)
        for i, output in enumerate(output_options):
            cm_dataview.write_file(filename[i], parts_list, fc_map, output)
            self.assertTrue(os.path.isfile(filename[i]))

    def test_read_files(self):
        filename = [os.path.join(mc.test_data_path, 'HH0_15_flag.txt')]
        parts, fc_map = cm_dataview.read_files(filename)
        self.assertTrue(parts[0] == 'HH0')

    # def tearDown(self):
    #     os.remove('testcorr.txt')
    #     os.remove('testflag.txt')

if __name__ == '__main__':
    unittest.main()

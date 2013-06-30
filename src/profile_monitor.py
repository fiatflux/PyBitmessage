# Periodically update a detailed log of profile data for use in statistical analysis of anomalous
# application behavior.
#
# Copyright 2013 Gregor Robinson <gregor@fiatflux.co.uk>.
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
# 
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
# 
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
# Example usage:
#     from profile_monitor import ProfileDataLogger
#     data_file = open('/tmp/testdatfile', 'w')
#     header_file = open('/tmp/testdatfile_headers', 'w+')
#     logger = ProfileDataLogger(data_file, header_file, interval=2).Start()
#     for i in range(kBigNumber):
#         DoSomething(i)
#     logger.Stop()

import operator
import os
import threading
import time
import yappi

class ProfileDataLogger:
    def __init__(self, data_file, header_file, interval=60):
        self.data_file = data_file
        self.headers = header_file
        self.column_number_map = {}
        self.current_line = []
        self.interval = interval

    def __del__(self):
        self.Stop()

    def Start(self):
        yappi.start()
        self.__RestartTimer()
        return self

    def Stop(self):
        self.timer.cancel()

    def __LogProfileData(self):
        # Make sure we have roughly same-length samples.
        yappi.stop()

        self.__ProcessCPUStats()
        for func_stats in yappi.get_func_stats():
            self.__ProcessFunctionStats(func_stats)

        self.__Emit()

        self.__RestartTimer()

        # Restart profiling.
        yappi.start()


    def __RestartTimer(self):
        self.timer = threading.Timer(self.interval, self.__LogProfileData)
        self.timer.daemon = True
        self.timer.start()

    # Associate a string column label with an unique column number.
    def __GetColumnNumber(self, key):
        if key in self.column_number_map:
            return self.column_number_map[key]
        else:
            self.column_number_map[key] = len(self.column_number_map) - 1
            self.current_line.append(0)
            assert len(self.column_number_map) == len(self.current_line)
            return self.column_number_map[key]

    def __ProcessCPUStats(self):
        for key, value in zip(('utime', 'stime', 'cutime', 'cstime', 'elapsed_time'),
                              os.times()):
            column_number = self.__GetColumnNumber(key)
            self.current_line[column_number] = value

    # Update current numbers for a particular stat entry (i.e. for a particular function).
    def __ProcessFunctionStats(self, stat_entry):
        function_name = stat_entry.full_name
        for stat_name, stat in zip(('callcount',      'ttot',          'tsub'),
                                   (stat_entry.ncall, stat_entry.ttot, stat_entry.tsub)):
            key = ' '.join(map(str, (function_name, stat_name)))
            column_number = self.__GetColumnNumber(key)
            self.current_line[column_number] = stat

    # Emit a line to the data file.
    def __Emit(self):
        self.data_file.write(','.join(map(str, self.current_line)))
        self.data_file.write('\n')
        self.data_file.flush()

        sorted_keys = [a[0] for a in sorted(self.column_number_map.items(), key=operator.itemgetter(1))]
        self.headers.seek(0, 0)
        self.headers.write('"')
        self.headers.write('","'.join(sorted_keys))
        self.headers.write('"\n')
        self.headers.flush()


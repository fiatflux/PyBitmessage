
import numpy
import sys

data_file = open(sys.argv[1], 'r')
sampling_window = 10.0

with open(sys.argv[2], 'r') as header_file:
    header_string = header_file.readline()

headers = header_string.split(',')

# Bijectively associate column number to descriptive data.
# TODO(fiatflux): Would be nice to further split these strings to break down different kinds of
#                 numbers into more logical pieces.
metadata_map = {}
for i, header_key in enumerate(headers):
    if ':' in header_key:
        # yappi info.
        trace_file_name, trace_rest = header_key.strip('"').split(':')
        trace_file_line_number, trace_method, trace_stat = trace_rest.split(' ')
    else:
        # os.times() info.
        trace_file_name = 'MAIN_PROCESS'
        trace_method = '__main__'
        trace_stat = header_key.strip('"')
        print(header_key)
    metadata_map[i] = (trace_file_name, trace_method, trace_stat)

last_data = numpy.zeros(len(headers))
data = numpy.zeros(len(headers))

for sample_number, line in enumerate(data_file.readlines()):
    raw_data = numpy.fromstring(line, dtype=float, sep=',')
    data[0:len(raw_data)] = raw_data
    if sample_number != 0:
        difference = data - last_data
        for colnum, stat in enumerate(difference):
            metadata = metadata_map[colnum]
            if metadata[2] == 'utime': # and stat / sampling_window > 0.01:
                print('Noticed significant processor use (%s) at sample %s.'
                      % (stat, sample_number))
    last_data = data

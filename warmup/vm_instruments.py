"""Parsers to deal with the data from instrumented VMs.
"""
import abc


def merge_instr_data(file_data):
    """Merge data from one or more instr_data JSON dictionaries.
    """
    instr_data = {'raw_vm_events': list()}
    for dict_ in file_data:
        instr_data['raw_vm_events'].append(dict_['raw_vm_events'])
    return instr_data


class ChartData(object):
    """Class to hold data needed by the plotting script.
    Each VM parser may parse a number of different events which need to be
    plotted (e.g. compilation events, GC, etc.). These should be stored in
    a list of ChartData objects, so that the plotting script does not have to
    know anything about the individual VMs.
    """

    def __init__(self, title, data, legend_text):
        self.title = title
        self.data = data
        self.legend_text = legend_text


class VMInstrumentParser(object):
    """Base class for VM instrumentation parsers.
    We expect one subclass per VM.
    """

    def __init__(self, vm):
        self.vm = vm
        self.chart_data = list()  # List of ChartData objects per p_exec.

    @abc.abstractmethod
    def parse_instr_data(self):
        """Parse VM instrumentation data.
        """
        return

class HotSpotInstrumentParser(VMInstrumentParser):
    """Parser for Oracle Hotspot instrumentation data.
    Data is in JSON format, and of the form:
      [iterNum, cumuCompTime, collectorInfo]

    Where collectorInfo is a list of the form:
      [collectorName, PoolNames, cumuCollectTime, cumuCollectCount]

    'cumu' means 'cumulative' and times are in milliseconds. collectorNames may
    'not be unique.

    Example line:
     [0, 17, [['PS Scavenge', ['PS Eden Space', 'PS Survivor Space'], 0, 0]]]
    """

    def __init__(self, instr_data):
        VMInstrumentParser.__init__(self, 'Hotspot')
        self.instr_data = instr_data['raw_vm_events'] if instr_data else None
        self.parse_instr_data()

    def parse_instr_data(self):
        if self.instr_data is None:
            return None
        for p_exec in xrange(len(self.instr_data)):
            iterations = len(self.instr_data[p_exec])
            cumulative_times = [self.instr_data[p_exec][i][1] for i in xrange(iterations)]
            times_secs = [cumulative_times[0] / 1000.0]
            for index in xrange(1, len(cumulative_times)):
                times_secs.append((cumulative_times[index] - cumulative_times[index - 1]) / 1000.0)
            assert len(times_secs) == len(cumulative_times)
            self.chart_data.append([ChartData('GC (secs)', times_secs, 'GC events')])


# Mapping from VM name -> parser class.
# This enables the main scripts to parse instrumentation data based only
# on the vm:bench:language triplets found in Krun data files.
INSTRUMENTATION_PARSERS = {'Hotspot': HotSpotInstrumentParser}

"""
The wmoc.network.geometry read in the geometry defined by EPANet
.inp file, and assign aditional parameters needed in transient
simution later in wmoc.

"""

from __future__ import print_function
import wntr
import matplotlib.pyplot as plt
import networkx as nx
import numpy as np
import logging
from wntr.network import WaterNetworkModel
import collections
from wmoc.network.control import valvesetting, pumpsetting

logger = logging.getLogger(__name__)

class TransientModel (WaterNetworkModel):
    """[summary]

    Parameters
    ----------
    WaterNetworkModel : [type]
        [description]
    """
    def __init__ (self, inp_file):
        super().__init__(inp_file)
        self.leak_node = []
        self.simulation_timestamps = []
        self.time_step = 0.
        self.simulation_peroid = 0.
        self.initial_velocity = []
        self.initial_head = []
        # assign ID to each links, start from 1.
        i =1
        for _, link in self.links():
            link.id = i
            i+=1

        # assign ID to each links, start from 1.
        i =1
        for _, node in self.nodes():
            node.id = i
            i+=1     ## Graph the network

        # calculate the slope for each pipe
        for _, pipe in self.pipes():
            try:
                theta = np.sin(np.arctan(pipe.end_node.elevation -
                    pipe.start_node.elevation)/pipe.length)
            except:
                theta = 0.0
            pipe.theta = theta
        
        # set operating defualt value as False
        for _, link in self.links():
            link.operating = False

    def set_wavespeed(self, wavespeed=1200.):

        if isinstance(wavespeed,float):
            # if wavespeed is a float, assign it to all pipes
            wavev = wavespeed * np.ones((self.num_pipes, 1))
        elif isinstance(wavespeed, (list,tuple,np.ndarray)):
            # if wavespeed is a list, assign each elements
            # to the respective pipes.
            if len(wavespeed) == self.num_pipes:
                wavev = wavespeed
            else:
                raise ValueError('The length of the wavespeed \
                input does not equal number of pipes. ')
        else:
            raise ValueError('Wavespeed should be a float or a list')

        # assign wave speed to each pipes
        i= 0
        for _, pipe in self.pipes():
            pipe.wavev = wavev[i]
            i+=1


    def add_leak(self, name=None, coeff=None, t0=0):
        """[summary]

        Parameters
        ----------
        name : list or str, optional
            The name of the leak nodes, by default None
        coeff : list or float, optional
            Emitter coefficient at the leak nodes, by default None
        t0 : int, optional
            [description], by default 0
        """
        # determine leak location based on input node name
        # and add the leak to initial condition calculation
        if name != None :
            for node in name:
                leak_node = self.get_node(node)
                leak_node.add_leak(self, area=coeff/np.sqrt(2*9.8),
                                    discharge_coeff = 1, start_time = t0)
                leak_node.emitter_coeff = coeff

                # set initial conditions as a new attribute to TransientModel
                self.leak_node.append(leak_node)

    def valve_closure(self, name=None, rule=None):
        valve = self.get_link(name)
        valve.operating = True
        valve.operation_rule = valvesetting(self.time_step, self.simulation_peroid, rule)

    def pump_shut_off(self, name=None, rule=None):
        pump = self.get_link(name)
        pump.operating = True
        pump.operation_rule = pumpsetting(self.time_step, self.simulation_peroid, rule)



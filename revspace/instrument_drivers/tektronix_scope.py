import pyvisa
import numpy as np
from typing import Literal

SERIAL_NUMBER = 'C047327'

def obtain_scope_address(serial_number):
    """
    Searches all resources and tries to identify an address
    linked to the input serial number.

    Args:
        serial_number (str):
            The input serial number of the device.
            For the Tektronix TDS 2024C it can be found in by pressing
            "Utility > System Status" in the front panel.

    """
    rm = pyvisa.ResourceManager()
    for resource_address in rm.list_resources():
        if serial_number in resource_address:
            print(f"Device with serial number {serial_number} was found with address '{resource_address}'.")
            return resource_address
    raise ValueError(f"Tektronix TDS 2024C with serial number {serial_number} was not found!")

def connect_to_scope(scope_address: int):

    rm = pyvisa.ResourceManager()
    scope = rm.open_resource(scope_address)

    scope.timeout = 10000  # 10 s (Tektronix instruments often need longer)
    scope.write("*RST")
    scope.write("*CLS")
    print('Successfully connected:', scope.query("*IDN?").strip())

    return scope


class Scope:

    def __init__(self,
                 serial_number = 'C047327'):
        
        scope_address = self.obtain_scope_address(serial_number)
        self.com = self.connect_to_scope(scope_address) # self.com is short for self.communications

        self.channels = ['CH1', 'CH2', 'CH3', 'CH4']
        self.ch_scale_min = 5e-3 # in units of [V]
        self.ch_scale_max = 5 # in units of [V]
        self.ch_scale_step = 0.01e-3 # in units of [V]
        self.ch_position_max = 10 # in units of [div]
        self.ch_position_min = -10 # in units of [div]
        self.ch_position_step = 0.04 # in units of [div]

        self.active_config = {'channels': {},
                              'global': {'horizontal scale [s/div]': 1e-6}}
        for channel in self.channels:
            self.active_config['channels'][channel] = {
                'state': 'OFF',
                'scale [V]': 1.0,
                'position [div]': 0.0,
                'coupling': 'DC',
                'bandwidth': 'OFF',
                'probe': 1,
                'invert': 'OFF'}

        # initialization
        print('Initializing instrument ...')
        self.com.write("ACQuire:STATE ON")
        self.com.write("LOCk NONe")
        self.com.write(f"HORizontal:SCAle {self.active_config['global']['horizontal scale [s/div]']}")
        
        for channel in self.channels:
            self.configure_channel(channel=channel,
                                   state=self.active_config['channels'][channel]['state'],
                                   scale=self.active_config['channels'][channel]['scale [V]'],
                                   position=self.active_config['channels'][channel]['position [div]'],
                                   coupling=self.active_config['channels'][channel]['coupling'],
                                   bandwidth=self.active_config['channels'][channel]['bandwidth'],
                                   probe=self.active_config['channels'][channel]['probe'],
                                   invert=self.active_config['channels'][channel]['invert'])
            print(f'Initialized channel {channel} ...')
        self.configure_channel(channel='CH1',
                               state='ON')
        print('Instrument initialized successfully!')


    def obtain_scope_address(self,
                             serial_number):
        """
        Searches all resources and tries to identify an address
        linked to the input serial number.

        Args:
            serial_number (str):
                The input serial number of the device.
                For the Tektronix TDS 2024C it can be found in by pressing
                "Utility > System Status" in the front panel.

        """
        rm = pyvisa.ResourceManager()
        for resource_address in rm.list_resources():
            if serial_number in resource_address:
                print(f"Device with serial number {serial_number} was found with address '{resource_address}'.")
                return resource_address
        raise ValueError(f"Tektronix TDS 2024C with serial number {serial_number} was not found!")
    
    def connect_to_scope(self,
                         scope_address: int):

        rm = pyvisa.ResourceManager()
        scope = rm.open_resource(scope_address)

        scope.timeout = 10000  # 10 s (Tektronix instruments often need longer)
        scope.write("*RST")
        scope.write("*CLS")
        print('Successfully connected:', scope.query("*IDN?").strip())

        return scope
    
    def configure_channel(self,
                          channel: Literal['CH1', 'CH2', 'CH3', 'CH4'],
                          state: Literal['ON', 'OFF'] = None,
                          scale: float = None,
                          position: float = None,
                          coupling: Literal['DC', 'AC', 'GND'] = None,
                          bandwidth: Literal['ON', 'OFF'] = None,
                          probe: Literal[1, 10, 20, 50, 100, 500, 1000] = None,
                          invert: Literal['ON', 'OFF'] = None):
        
        if channel not in ['CH1', 'CH2', 'CH3', 'CH4']:
            raise ValueError(f"Invalid channel input. Valid input options are: ['CH1', 'CH2', 'CH3', 'CH4'].")
        
        if state is not None:
            if state not in ['ON', 'OFF']:
                raise ValueError(f"Invalid state input. Valid input options are: ['ON', 'OFF'].")
            self.com.write(f"SELECT:{channel} {state}")
            self.active_config['channels'][channel]['state'] = state

        # it is important to set the probe prior to setting the scale!
        if probe is not None:
            if probe not in [1, 10, 20, 50, 100, 500, 1000]:
                raise ValueError(f"Invalid probe input. Valid input options are: [1, 10, 20, 50, 100, 500, 1000].") 
            self.com.write(f"{channel}:PRObe {probe}")
            self.active_config['channels'][channel]['probe'] = probe

        if scale is not None:
            scale_valid_inputs = np.round(np.arange(self.ch_scale_min,
                                           self.ch_scale_max+self.ch_scale_step,
                                           self.ch_scale_step), 5)
            if scale not in scale_valid_inputs:
                raise ValueError("Invalid scale input. Valid input options are within "
                                 f"[{self.ch_scale_min} V, {self.ch_scale_max} V] with step size {self.ch_scale_step} V.")
            self.com.write(f"{channel}:SCAle {scale}")
            self.active_config['channels'][channel]['scale [V]'] = scale
            
        if position is not None:
            position_valid_inputs = np.round(np.arange(self.ch_position_min,
                                             self.ch_position_max+self.ch_position_step,
                                             self.ch_position_step), 2)
            if position not in position_valid_inputs:
                raise ValueError("Invalid position input. Valid input options are within "
                                 f"[{self.ch_position_min} div, {self.ch_position_max} div] with step size {self.ch_position_step} div.")
            self.com.write(f"{channel}:POSition {position}")
            self.active_config['channels'][channel]['position [div]'] = position

        if coupling is not None:
            if coupling not in ['DC', 'AC', 'GND']:
                raise ValueError(f"Invalid coupling input. Valid input options are: ['DC', 'AC', 'GND'].")
            self.com.write(f"{channel}:COUPling {coupling}")
            self.active_config['channels'][channel]['coupling'] = coupling

        if bandwidth is not None:
            if bandwidth not in ['ON', 'OFF']:
                raise ValueError(f"Invalid bandwidth input. Valid input options are: ['ON', 'OFF'].")
            self.com.write(f"{channel}:BANdwidth {bandwidth}")
            self.active_config['channels'][channel]['bandwidth'] = bandwidth

        if invert is not None:
            if invert not in ['ON', 'OFF']:
                raise ValueError(f"Invalid invert input. Valid input options are: ['ON', 'OFF'].")
            self.com.write(f"{channel}:INVert {invert}")
            self.active_config['channels'][channel]['invert'] = invert
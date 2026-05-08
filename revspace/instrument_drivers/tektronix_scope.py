import pyvisa

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

        self.configuration = {
            'channels': {},
            'global': {'horizontal scale [s/div]': 1e-6}
        }
        for channel in ['CH1', 'CH2', 'CH3', 'CH4']:
            self.configuration['channels'][channel] = {'state': 'OFF',
                                                        'coupling': 'DC',
                                                        'bandwidth': 'OFF',
                                                        'probe [X]': 1,
                                                        'invert': 'OFF',
                                                        'scale [V]': 1.0,
                                                        'position [V]': 0.0}

        # initialization
        self.com.write("ACQuire:STATE ON")
        self.com.write("LOCk NONe")
        self.com.write(f"HORizontal:SCAle {self.configuration['global']['horizontal scale [s/div]']}")
        
        for channel in ['CH1', 'CH2', 'CH3', 'CH4']:
            self.com.write(f"SELECT:{channel} OFF")
            self.com.write(f"{channel}:COUPling DC") # available options: AC, DC, GND
            self.com.write(f"{channel}:BANdwidth OFF") # can be OFF, ON
            self.com.write(f"{channel}:PRObe 1") # sets the probe attenuation to 1X, can be {1 | 10 | 20 | 50 | 100 | 500 | 1000}
            self.com.write(f"{channel}:INVert OFF") # can be OFF, ON
            self.com.write(f"{channel}:SCAle {self.configuration['channels'][channel]['scale [V]']}")
            self.com.write(f"{channel}:POSition {self.configuration['channels'][channel]['position [V]']}")
        self.com.write(f"SELECT:CH1 ON") # turn on only CH1


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
    
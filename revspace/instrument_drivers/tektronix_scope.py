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
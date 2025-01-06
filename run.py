import pyvisa
from datetime import datetime, timezone
import time
import signal
import sys

# Constant: MJD epoch
MJD_EPOCH = datetime(1858, 11, 17, 0, 0, 0, tzinfo=timezone.utc)

def get_modified_julian_date():
    """
    Calculates the Modified Julian Date (MJD) using the epoch.
    """
    now = datetime.now(timezone.utc)  # Current time in UTC
    delta = now - MJD_EPOCH  # Time difference
    mjd = delta.days + delta.seconds / 86400.0 + delta.microseconds / 86400.0 / 1e6  # Microsecond precision
    return mjd

def dso_init(ip_address):
    """
    Initializes the Keysight DSOX1204G oscilloscope, setting up the initial parameters.
    """
    rm = pyvisa.ResourceManager()
    resource_name = f"TCPIP::{ip_address}::INSTR"
    scope = rm.open_resource(resource_name)
    print(f"Connected to: {scope.query('*IDN?').strip()}")

    # onlu tests...
    # print(f"-> {scope.query(':CHANnel1:SCALe?').strip()}")

    # Oscilloscope settings
    scope.write(":MEASure:SOURce CHANnel1")  # Select measurement source channel
    scope.write(":MEASure:FREQuency")       # Set frequency measurement
    scope.write(":CHANnel1:BWL OFF")        # No bandwidth limit
    scope.write(":TRIGger:EDGE:SOURce CHANnel1")  # Trigger source optimization
    scope.write(":TRIGger:EDGE:LEVel 2")   # Set trigger level to 2 V

    # Optional settings
    # scope.write(":TIMebase:SCALe 6.0E-8")  # Set horizontal time resolution to 60 nanoseconds per division

    return scope

def measure_frequency(scope, n=10):
    query_command = ":MEASure:FREQuency?"
    total = sum(float(scope.query(query_command)) for _ in range(n))
    return total / n

def dso_close(scope):
    """
    Closes the connection with the oscilloscope.
    """
    print("Closing the oscilloscope connection...")
    scope.close()

def frequency_to_period_scientific(frequency):
    """
    Converts frequency to period in scientific notation.
    """
    if frequency <= 0:
        raise ValueError("Frequency must be greater than zero.")

    period = 1 / frequency

    # Return in required format
    return f"{period:.20E}"

# Define the handler for SIGINT (Ctrl-C)
def handle_sigint(signal, frame):
    """
    Handle SIGINT (Ctrl-C) to close the oscilloscope connection and exit cleanly.
    """
    print("\nCtrl-C detected. Closing the oscilloscope and exiting...")
    dso_close(scope)  # Close oscilloscope connection
    sys.exit(0)  # Exit the program cleanly

# Set up the signal handler for SIGINT (Ctrl-C)
signal.signal(signal.SIGINT, handle_sigint)

if __name__ == "__main__":

    sys.stdout = open("timedata.txt", "w", buffering=1)

    # IP address of the oscilloscope
    ip_address = "192.168.1.100"

    # Initialize the oscilloscope
    scope = dso_init(ip_address)

    first_time = True
    N = 19      # sample per one measurement
    M = 30000   # numer of measurements

    # while True:
    for _ in range(M):
        # Display the number of samples
        if first_time:
            print(f"Number of samples: {N}")

        # Measure execution time
        start_time = time.time()  # Start time in seconds
        avg_frequency = measure_frequency(scope, n=N)
        end_time = time.time()  # End time in seconds

        # Convert frequency to period
        period = frequency_to_period_scientific(avg_frequency)

        # Retrieve the Modified Julian Date (MJD) timestamp
        mjd = get_modified_julian_date()

        # Calculate execution time in milliseconds
        elapsed_time_ms = (end_time - start_time) * 1000  # Convert to milliseconds

        # Display the results
        if first_time:
            print(f"[MJD: {mjd:.5f}] Averaged frequency: {avg_frequency / 1e6:.6f} MHz, period: {period}")
            print(f"Elapsed time: {elapsed_time_ms:.2f} ms\n")

        print(f"measurements counter={period},gate={elapsed_time_ms:.2f} {mjd:.5f}")

        first_time = False

    dso_close(scope)  # Close oscilloscope connection


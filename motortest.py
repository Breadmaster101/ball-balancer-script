from gpiozero import DigitalOutputDevice
from time import sleep

# --- Pin Definitions (BCM Numbering) ---
DIR_PIN = 22
STEP_PIN = 27
EN_PIN = 17

# --- Initialize the Pins ---
# DigitalOutputDevice defaults to LOW (False) when initialized
direction = DigitalOutputDevice(DIR_PIN)
step = DigitalOutputDevice(STEP_PIN)
enable = DigitalOutputDevice(EN_PIN)

def spin_motor(steps, delay, dir_value):
    """
    Spins the motor a set number of steps.
    delay: time between pulses (controls speed)
    dir_value: True (1) or False (0) for clockwise/counter-clockwise
    """
    # Set the direction
    direction.value = dir_value
    
    # Generate the step pulses
    for _ in range(steps):
        step.on()
        sleep(delay)
        step.off()
        sleep(delay)

try:
    print("Enabling motor driver...")
    # EN pin is active-LOW. Set to False to turn the motor ON.
    enable.off() 
    sleep(0.5) # Brief pause to let the coils energize

    # At 1/16th microstepping, 3200 steps = 1 full revolution
    # We will do 16000 steps to get 5 full noticeable revolutions
    
    print("Spinning Forward...")
    spin_motor(steps=16000, delay=0.0002, dir_value=True)
    
    sleep(1) # Pause for a second
    
    print("Spinning Backward...")
    spin_motor(steps=16000, delay=0.0002, dir_value=False)

except KeyboardInterrupt:
    print("\nTest interrupted by user.")

finally:
    print("Disabling motor driver and cleaning up...")
    # Set EN pin HIGH to cut power to the motor coils (frees the motor)
    enable.on()
    
    # Close the pin connections safely
    direction.close()
    step.close()
    enable.close()
    print("Done!")

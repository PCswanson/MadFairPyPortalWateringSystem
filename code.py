import time
import board
import busio
from digitalio import DigitalInOut
from analogio import AnalogIn
from time import sleep

# ESP32 SPI
from adafruit_esp32spi import adafruit_esp32spi, adafruit_esp32spi_wifimanager

# Import NeoPixel Library
import neopixel

# Import Adafruit IO HTTP Client
from adafruit_io.adafruit_io import IO_HTTP, AdafruitIO_RequestError

from board import SCL, SDA
import busio

from adafruit_seesaw.seesaw import Seesaw

i2c_bus = busio.I2C(SCL, SDA)

ss = Seesaw(i2c_bus, addr=0x36)

# Timeout between sending data to Adafruit IO, in seconds
IO_DELAY = 30

try:
    from secrets import secrets
except ImportError:
    print("WiFi secrets are kept in secrets.py, please add them there!")
    raise

# PyPortal ESP32 Setup
esp32_cs = DigitalInOut(board.ESP_CS)
esp32_ready = DigitalInOut(board.ESP_BUSY)
esp32_reset = DigitalInOut(board.ESP_RESET)
spi = busio.SPI(board.SCK, board.MOSI, board.MISO)
esp = adafruit_esp32spi.ESP_SPIcontrol(spi, esp32_cs, esp32_ready, esp32_reset)

wifi = adafruit_esp32spi_wifimanager.ESPSPI_WiFiManager(esp, secrets)

ADAFRUIT_IO_USER = secrets['aio_username']
ADAFRUIT_IO_KEY = secrets['aio_key']

# Create an instance of the Adafruit IO HTTP client
io = IO_HTTP(ADAFRUIT_IO_USER, ADAFRUIT_IO_KEY, wifi)

try:

    # Get the 'temperature' feed from Adafruit IO
    temperature_feed = io.get_feed('pyportalplant.temp')
    moisture_feed = io.get_feed('pyportalplant.moisture')
    set_feed = io.get_feed('pyportalplant.waterlevelset')

except AdafruitIO_RequestError:
    # If no 'temperature' feed exists, create one
    temperature_feed = io.create_new_feed('pyportalplant.temp')
    moisture_feed = io.create_new_feed('pyportalplant.moisture')
    set_feed = io.create_new_feed('pyportalplant.waterlevelset')

while True:
    try:

        # read moisture level through capacitive touch pad
        touch = ss.moisture_read()

        # read temperature from the temperature sensor
        temp = ss.get_temp()

        #get waterlevelset data from AIO
        data = io.receive_data(set_feed['key'])
        set_value = data.get('value',0)

        print("temp: " + str(temp) + "  moisture: " + str(touch) + " water level: " + str(set_value))
        print('Sending to Adafruit IO...')

        io.send_data(moisture_feed['key'], touch)
        io.send_data(temperature_feed['key'], temp, precision=2)
        print('Sent to Adafruit IO!')
    except (ValueError, RuntimeError) as e:
        print("Failed to get data, retrying\n", e)
        wifi.reset()
        continue

    if int(set_value)*10 > touch :
        print("pump on")
        sleep(3)
        print("pump off")
    else:
        print("moisture ok")

    time.sleep(60)


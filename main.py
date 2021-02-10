#!/usr/bin/python3
# -*- coding:utf-8 -*-

# *************************************************** 
#   This is a example program for
#   a Weather Station using Raspberry Pi B+, Waveshare ePaper Display and ProtoStax enclosure
#   --> https://www.waveshare.com/product/modules/oleds-lcds/e-paper/2.7inch-e-paper-hat-b.htm
#   --> https://www.protostax.com/products/protostax-for-raspberry-pi-b
#
#   It uses the weather API provided by Open Weather Map (https://openweathermap.org/api) to
#   query the current weather for a given location and then display it on the ePaper display.
#   It refreshes the weather information every 10 minutes and updates the display.
#   Written by Sridhar Rajagopal for ProtoStax.
#   BSD license. All text above must be included in any redistribution
# *

import os
import sys
import requests
import configparser
import time
import signal
import traceback
import pyowm
from PIL import Image, ImageDraw, ImageFont

sys.path.append(os.path.join(sys.path[0], 'lib'))

import epd2in7b
import epdconfig

if sys.version_info[0] < 3:
    raise Exception("Must be using Python 3")

config = configparser.ConfigParser()
config.read('config.ini')

owm = pyowm.OWM(config['General']['owm_api_key'])

# Find your own city id here: 
# http://bulk.openweathermap.org/sample/city.list.json.gz
# Replace city_id below with the city id of your choice
#

# REPLACE WITH YOUR CITY ID
city_id = int(config['General']['owm_city'])

# Refer to http://www.alessioatzeni.com/meteocons/ for the mapping of meteocons to characters,
# and modify the dictionary below to change icons you want to use for different weather conditions!
# Meteocons is free to use - you can customize the icons - do consider contributing back to Meteocons!

weather_icon_dict = {
    200: "6", 201: "6", 202: "6", 210: "6", 211: "6", 212: "6",
    221: "6", 230: "6", 231: "6", 232: "6",

    300: "7", 301: "7", 302: "8", 310: "7", 311: "8", 312: "8",
    313: "8", 314: "8", 321: "8",

    500: "7", 501: "7", 502: "8", 503: "8", 504: "8", 511: "8",
    520: "7", 521: "7", 522: "8", 531: "8",

    600: "V", 601: "V", 602: "W", 611: "X", 612: "X", 613: "X",
    615: "V", 616: "V", 620: "V", 621: "W", 622: "W",

    701: "M", 711: "M", 721: "M", 731: "M", 741: "M", 751: "M",
    761: "M", 762: "M", 771: "M", 781: "M",

    800: "1",

    801: "H", 802: "N", 803: "N", 804: "Y"
}


def get_temperature(device):
    ha_api_host = config['General']['ha_api_host']
    ha_api_key = config['General']['ha_api_key']
    ha_device = config['General'][device]

    url = f"{ha_api_host}/api/states/{ha_device}"
    headers = {
        "Authorization": f"Bearer {ha_api_key}",
        "content-type": "application/json",
    }

    response = requests.get(url, headers=headers)
    data = response.json()

    return data['state']


def main():
    epd = epd2in7b.EPD()

    # Get Weather data from OWM
    obs = owm.weather_at_id(city_id)
    location = obs.get_location().get_name()
    weather = obs.get_weather()
    reftime = weather.get_reference_time()
    description = weather.get_detailed_status()
    temperature = weather.get_temperature(unit='celsius')
    humidity = weather.get_humidity()
    pressure = weather.get_pressure()
    clouds = weather.get_clouds()
    wind = weather.get_wind()
    rain = weather.get_rain()
    sunrise = weather.get_sunrise_time()
    sunset = weather.get_sunset_time()

    temperature_outside = get_temperature('ha_device_one')
    temperature_bedroom = get_temperature('ha_device_two')

    print("location: " + location)
    print("weather: " + str(weather))
    print("description: " + description)
    print("temperature: " + str(temperature))
    print("temperature_outside: " + str(temperature_outside))
    print("temperature_bedroom: " + str(temperature_bedroom))
    print("humidity: " + str(humidity))
    print("pressure: " + str(pressure))
    print("clouds: " + str(clouds))
    print("wind: " + str(wind))
    print("rain: " + str(rain))
    print("sunrise: " + time.strftime('%H:%M', time.localtime(sunrise)))
    print("sunset: " + time.strftime('%H:%M', time.localtime(sunset)))

    # Display Weather Information on e-Paper Display
    try:
        # print("Clear...")
        epd.init()
        epd.Clear()

        # Drawing on the Horizontal image
        HBlackimage = Image.new('1', (epd2in7b.EPD_HEIGHT, epd2in7b.EPD_WIDTH), 255)  # 298*126

        # print("Drawing")
        drawblack = ImageDraw.Draw(HBlackimage)

        font24 = ImageFont.truetype('fonts/arial.ttf', 24)
        font16 = ImageFont.truetype('fonts/arial.ttf', 16)
        font20 = ImageFont.truetype('fonts/arial.ttf', 20)
        fontweather = ImageFont.truetype('fonts/meteocons-webfont.ttf', 30)
        fontweatherbig = ImageFont.truetype('fonts/meteocons-webfont.ttf', 60)

        w1, h1 = font24.getsize(location)
        w2, h2 = font20.getsize(description)
        w3, h3 = fontweatherbig.getsize(weather_icon_dict[weather.get_weather_code()])

        drawblack.text((10, 0), location, font=font24, fill=0)
        drawblack.text((10 + (w1 / 2 - w2 / 2), 25), description, font=font20, fill=0)
        drawblack.text((264 - w3 - 10, 0), weather_icon_dict[weather.get_weather_code()], font=fontweatherbig, fill=0)
        drawblack.text((10, 45), "Observed at: " + time.strftime('%I:%M %p', time.localtime(reftime)), font=font16,
                       fill=0)

        temp_out = str("{0}{1}C".format(temperature_outside, u'\u00b0'))
        w4, h4 = font24.getsize(temp_out)
        drawblack.text((10, 80), temp_out, font=font24, fill=0)
        drawblack.text((10 + w4, 80), "'", font=fontweather, fill=0)

        temp_bed = str("{0}{1}C".format(temperature_bedroom, u'\u00b0'))
        w4, h4 = font24.getsize(temp_bed)
        drawblack.text((150, 80), temp_bed, font=font24, fill=0)
        drawblack.text((150 + w4, 80), "'", font=fontweather, fill=0)

        drawblack.text((20, 110), "Outside", font=font20, fill=0)
        drawblack.text((160, 110), "Bedroom", font=font20, fill=0)

        drawblack.text((20, 150), str("min {0}{1}          {2}{3} max".format(
            int(round(temperature['temp_min'])), u'\u00b0',
            int(round(temperature['temp_max'])), u'\u00b0')),
                       font=font24, fill=0)
        # drawblack.text((40, 120), "A", font=fontweather, fill=0)
        # drawblack.text((185, 120), "J", font=fontweather, fill=0)
        # drawblack.text((20, 150), time.strftime('%I:%M %p', time.localtime(sunrise)), font=font20, fill=0)
        # drawblack.text((160, 150), time.strftime('%I:%M %p', time.localtime(sunset)), font=font20, fill=0)

        epd.display(epd.getbuffer(HBlackimage))
        time.sleep(2)


    except IOError as e:
        print('traceback.format_exc():\n%s', traceback.format_exc())

    epdconfig.module_init()
    epd.sleep()
    exit(0)


# gracefully exit without a big exception message if possible
def ctrl_c_handler(signal, frame):
    # print('Goodbye!')
    epdconfig.module_init()
    epdconfig.module_exit()
    exit(0)


signal.signal(signal.SIGINT, ctrl_c_handler)

if __name__ == '__main__':
    main()

from luma.core.interface.serial import i2c, spi
from luma.core.render import canvas
from luma.oled.device import sh1106
from time import sleep
from datetime import datetime, time, timezone, timedelta
import Adafruit_DHT as adht
import psutil
import os
import socket
import netifaces as ni
from typing import Optional
import docker
import RPi.GPIO as GPIO
from threading import Thread
import subprocess


def get_cpu_temp():

    result = 0.0
    if os.path.isfile('/sys/class/thermal/thermal_zone0/temp'):
        with open('/sys/class/thermal/thermal_zone0/temp') as f:
            line = f.readline().strip()
        if line.isdigit():
            result = float(line) / 1000
    return result


button1 = 40
button2 = 37
screenday = False
cpu_temp = str(round(float(get_cpu_temp()),2))
cpu_percent = str(psutil.cpu_percent(4))
screennb = 0
photoresistorpin = 36
humidity,temp = adht.read_retry(adht.DHT22, 4)


def get_ip_address(ifname):
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    return socket.inet_ntoa(fcntl.ioctl(
        s.fileno(),
        0x8915,  # SIOCGIFADDR
        struct.pack('256s', ifname[:15])
    )[20:24])


def setup1():
    GPIO.setmode(GPIO.BOARD)
    GPIO.setup(button1, GPIO.IN)


def loop1():
    global screenday
    while True:
        button_state = GPIO.input(button1)
        if  button_state == False:

            while GPIO.input(button1) == False:
                sleep(0.2)
            if screenday == True :
                screenday = False
            else :
                screenday = True


def setup2():
    GPIO.setmode(GPIO.BOARD)
    GPIO.setup(button2, GPIO.IN)


def loop2():
    global screennb
    while True:
        button_state = GPIO.input(button2)
        if  button_state == False:

            while GPIO.input(button2) == False:
                sleep(0.2)
            if screennb == 0 :
                screennb = 1
            elif screennb ==1:
                screennb = 2
            elif screennb == 2:
                screennb = 3
            elif screennb == 3:
                screennb = 0


def setup3():

    GPIO.setmode(GPIO.BOARD)
    #Output on the pin for
    GPIO.setup(photoresistorpin, GPIO.OUT)
    GPIO.output(photoresistorpin, GPIO.LOW)
    sleep(0.1)

    #Change the pin back to input
    GPIO.setup(photoresistorpin, GPIO.IN)


def photoresistor():
    global light
    while True:
        photolight = GPIO.input(photoresistorpin)
        if (photolight == GPIO.LOW):
            light = False
            sleep(1)

        else:
            light = True
            sleep(1)


def temphumid():
    global humidity
    global temp
    while True:
        humidity,temp = adht.read_retry(adht.DHT22, 4)
        sleep(20)


def getcpu():
    global cpu_temp
    global cpu_percent
    while True:
        cpu_temp = str(round(float(get_cpu_temp()),2))
        cpu_percent = str(psutil.cpu_percent(4))


def main():
    onetime = True
    serial = i2c(port=1, address=0x3C)
    # substitute ssd1331(...) or sh1106(...) below if using that device
    ni.ifaddresses('eth0')
    IP_addres = ni.ifaddresses('eth0')[ni.AF_INET][0]['addr']
    device = sh1106(serial)
    docker = ["YOUR_DOCKER_CONTAINER"]

    while True:
        if(light == True or screenday == True):
            if(screennb == 0):
                with canvas(device) as draw:
                    now = datetime.now()
                    time1 = now + timedelta(seconds=2)
                    draw.text((0, 0)," CPU : " +  cpu_percent +"%, "  + cpu_temp+"°C  " , fill="white")
                    draw.text((0, 50)," Humidity : " +  str(round(float(humidity),2))+"%", fill="white")
                    draw.text((0, 40)," Temp : " +  str(round(float(temp),2))+"°C", fill="white")
                    draw.text((0, 20)," IP : " +  str(IP_addres), fill="white")
                    draw.text((0,10), " Mem : " + str(psutil.virtual_memory()[2]) +"%", fill="white")

            elif(screennb == 1):
                with canvas(device) as draw:
                    draw.text((0,0)," Screen : " + str(screenday), fill="white")

            elif(screennb == 2):
                with canvas(device) as draw:
                    draw.text((0,0)," Docker started : " , fill="white")
                    line = 20
                    for i in range(4) :
                        if is_container_running(docker[i]) == True :
                            draw.text((0,line), docker[i], fill = "white")
                            line = line + 10

            elif(screennb == 3):
                if(len(docker) > 4) :
                    with canvas(device) as draw:
                        if(len(docker) < 10 ):
                            number = len(docker)
                        else :
                            number = 10
                        line = 0
                        for i in range(4, number) :
                            if is_container_running(docker[i]) == True :
                                draw.text((0,line), docker[i], fill = "white")
                                line = line + 10

        else:
            with canvas(device) as draw:
                draw.rectangle(device.bounding_box, fill="black")



def in_between(now, start, end):
    if start <= end:
        return start <= now < end
    else: # over midnight e.g., 23:30-04:15
        return start <= now or now < end

def testtime():
    timezone_offset = +1.0
    tzinfo = timezone(timedelta(hours=timezone_offset))
    if in_between(datetime.now(tzinfo).time(), time(22,30), time(9,00)) :
        return "night"
    else:
        return "day"



def is_container_running(container_name: str) -> Optional[bool]:

    RUNNING = "running"
    docker_client = docker.from_env()

    try:
        container = docker_client.containers.get(container_name)
    except docker.errors.NotFound as exc:
      print("error")

    else:
        container_state = container.attrs["State"]
        return container_state["Status"] == RUNNING

if __name__ == "__main__":
    #container_name = "pihole"
    #result = is_container_running(container_name)
    #print(result)
    setup1()
    setup2()
    setup3()

    p = Thread( target=main)
    p1 = Thread( target=loop1)
    p2 = Thread( target=getcpu)
    p3 = Thread( target=loop2)
    p4 = Thread( target=photoresistor)
    p5 = Thread(target = temphumid)

    p.start()
    p1.start()
    p2.start()
    p3.start()
    p4.start()
    p5.start()

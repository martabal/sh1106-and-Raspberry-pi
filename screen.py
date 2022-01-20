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
button1 = 40
button2 = 38
screenday = True
screennight = False



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
                screen = True
def setup2():
    GPIO.setmode(GPIO.BOARD)
    GPIO.setup(button2, GPIO.IN)

def loop2():
    global screennight
    while True:
        button_state = GPIO.input(button2)
        if  button_state == False:

            while GPIO.input(button2) == False:
                sleep(0.2)
            if screennight == True :
                screennight = False
            else :
                screennight = True
def main():

    serial = i2c(port=1, address=0x3C)
    # substitute ssd1331(...) or sh1106(...) below if using that device
    h,t = adht.read_retry(adht.DHT22, 4)
    ni.ifaddresses('eth0')
    IP_addres = ni.ifaddresses('eth0')[ni.AF_INET][0]['addr']
    now = datetime.now()
    time1 = now + timedelta(seconds=2)
    time2 = now + timedelta(seconds=30)
    device = sh1106(serial)
    while 1==1:

        with canvas(device) as draw:
            cpu_temp = get_cpu_temp()


            if((testtime() == "day" and screenday == True) or (testtime() == "night" and screennight == True)):
                now = datetime.now()
                if(time2 < now):
                    now = datetime.now()
                    time2 = now + timedelta(seconds=30)
                    h,t = adht.read_retry(adht.DHT22, 4)
                if(time1 < now) :
                    now = datetime.now()
                    time1 = now + timedelta(seconds=2)
                    draw.text((0, 0),"CPU : " +  str(psutil.cpu_percent(4)) +"%, " + str(round(float(cpu_temp),2)) +"°C", fill="white")
                    draw.text((0, 10),"Temp : " +  str(round(float(h),2)), fill="white")
                    draw.text((0, 20),"Humidity : " +  str(round(float(t),2)), fill="white")
                    draw.text((0, 30),"IP : " +  str(IP_addres), fill="white")
            else:
                draw.rectangle(device.bounding_box, fill="black")



def in_between(now, start, end):
    if start <= end:
        return start <= now < end
    else: # over midnight e.g., 23:30-04:15
        return start <= now or now < end

def testtime():
    timezone_offset = +1.0
    tzinfo = timezone(timedelta(hours=timezone_offset))
    if in_between(datetime.now(tzinfo).time(), time(23,30), time(8,30)) :
        return "night"
    else:
        return "day"

def get_cpu_temp():
    """
    Obtains the current value of the CPU temperature.
    :returns: Current value of the CPU temperature if successful, zero value otherwise.
    :rtype: float
    """
    # Initialize the result.
    result = 0.0
    # The first line in this file holds the CPU temperature as an integer times 1000.
    # Read the first line and remove the newline character at the end of the string.
    if os.path.isfile('/sys/class/thermal/thermal_zone0/temp'):
        with open('/sys/class/thermal/thermal_zone0/temp') as f:
            line = f.readline().strip()
        # Test if the string is an integer as expected.
        if line.isdigit():
            # Convert the string with the CPU temperature to a float in degrees Celsius.
            result = float(line) / 1000
    # Give the result back to the caller.
    return result


def is_container_running(container_name: str) -> Optional[bool]:
    """Verify the status of a container by it's name

    :param container_name: the name of the container
    :return: boolean or None
    """
    RUNNING = "running"
    # Connect to Docker using the default socket or the configuration
    # in your environment
    docker_client = docker.from_env()
    # Or give configuration
    # docker_socket = "unix://var/run/docker.sock"
    # docker_client = docker.DockerClient(docker_socket)

    try:
        container = docker_client.containers.get(container_name)
    except docker.errors.NotFound as exc:
        print(f"Check container name!\n{exc.explanation}")
    else:
        container_state = container.attrs["State"]
        return container_state["Status"] == RUNNING

if __name__ == "__main__":
    #container_name = "pihole"
    #result = is_container_running(container_name)
    #print(result)
    setup1()
    setup2()
    p2 = Thread( target=loop2)
    p1 = Thread( target=loop1)
    p = Thread( target=main)
    p2.start()
    p1.start()
    p.start()

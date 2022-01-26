# sh1106-and-Raspberry-pi

Add screen.py to your crontab


Connect your GND and VDD pins to your ground and 3.3V raspberry pins.
Connect the photoresistor to pin 36, one button to turn on/off your screen to pin 40 and the button to switch screens to pin 37.
Protect your buttons with 10k ohm resistor and add resistors in parallel to have a photoresistor more sensitive to light.

Install requirements by executing 

   ```shell
   sudo sh setup.sh
   ```
Then you can add the script to cron with

   ```shell
   sudo crontabe -e
   ```  
and add

   ```shell
   @reboot python3 ~/sh1106-and-Raspberry-pi/screen.py
   ```  

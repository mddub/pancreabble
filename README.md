# pancreabble

Send OpenAPS status updates to a Pebble watch via Bluetooth.

## Rationale

To monitor an [OpenAPS artificial pancreas system](https://github.com/openaps/docs) in real-time, a typical setup looks like:
```
Raspberry Pi/Intel Edison -> network -> Nightscout server -> network -> smartphone
                                                                     |
                                                                     -> smartwatch
                                                                     |
                                                                     -> laptop
```

In the best case, you're somewhere like a home or office, where your Pi/Edison has already been configured to connect to the wifi. When that's not possible, you can enable a personal hotspot on your phone (until your phone dies, at least).

But in many cases (on a plane, on a long cycling or hiking trip, overseas, underground), you don't have internet, and the whole beautiful constellation of network hops fizzles away. In those cases you should use something like Pancreabble.
```
Raspberry Pi/Intel Edison -> Bluetooth -> Pebble watch
```

## Using it in your loop: notifications

1. Format your loop state as a subject and message, and send them to the Pebble as a notification:
  ```
  openaps use pbl notify "`python pebble_subject.py`" "`python pebble_message.py`"
  ```

  (This assumes you've written `pebble_subject.py` / `pebble_message.py` to summarize the relevant bits of your loop state in the way you want.)

1. Take off the watch band, leave your Pebble on the "Notifications" screen, and whoa you just added an e-ink screen to your APS:

  ![](http://i.imgur.com/hapQB8I.jpg)

## Using it in your loop: Urchin CGM

1. Pair the Pebble with your phone, and use your phone to install [Urchin](https://github.com/mddub/urchin-cgm).

1. Open the Urchin settings page in the Pebble app on your phone. Configure the graph and layout. Under "Update Settings", make sure the frequency is set to "When CGM reading expected".

1. Forget the Pebble/phone pairing, and pair the Pebble with the Pi/Edison using the setup instructions below. (If it was previously paired, you may need to [forget and re-pair it](https://gist.github.com/0/c73e2557d875446b9603).)

1. For accurate display of CGM recency, it is highly recommended to add a report which reads the CGM clock. Here's what that might look like for Dexcom (make sure it is connected via cable):
  ```
  openaps report add monitor/dex-clock.json JSON cgm ReadDisplayTime
  ```

1. At the end of your loop, use `format_urchin_data` to prepare the data, and `send_urchin_data` to send it:
  ```
  # You'll want to generate your own loop summary to show in the status line.
  echo '{"message": "loop status at '$(date +%-I:%M%P)': copacetic"}' > urchin-status.json

  openaps report add urchin-data.json JSON pbl format_urchin_data \
    monitor/dex-glucose.json \
    # Make sure you've read the CGM display clock earlier in your loop:
    --cgm-clock monitor/dex-clock.json \
    # ...and called whatever generates your loop summary message:
    --status-json urchin-status.json

  openaps report invoke urchin-data.json

  # Consider making this a report, too
  openaps use pbl send_urchin_data urchin-data.json
  ```

  ![](http://i.imgur.com/n5dcNj1.jpg)

See `openaps use pbl format_urchin_data --help` for more options.


## Using it in your loop: Urchin CGM -- An alternate approach as provided by Matt Pressnall
What I do is set two different scripts to run to keep the Pebble updated...this is separate from the crontab "loop" but relies a bit on some the data that the loop generates.  It, also, generates its own data to make sure things will run.  Lastly, it has been 9 months since I touched any of this so I may have forgotten a few things.  I hacked and jammed to make this work...I did NOT follow best practices.

Here's what my cron looks like for these extra scripts:
````
# update the Pebble with new data...try every minute
* * * * * /bin/bash /home/pi/multiloop/scripts/update-pebble.sh
# as soon as we reboot, let's put something on the watch...even old data (maybe a bad idea but we know we are connected as soon as the rig comes up).
@reboot /bin/bash /home/pi/multiloop/scripts/pebble-watchface-update.sh
````

And the scripts.

You should run each of these commands one at a time in update-pebble.sh to see where things might bomb out.
````
#!/bin/bash
#update-pebble.sh - runs every minute
cd /home/pi/multiloop
# format the cgm file for localized use...do this hacky sed replacement that will fail for any timezone other than Pacific...the report needs the timezone data stripped off so do it.  Replace with whatever offset your timezone has from UTC. (8 or 7 hours for Pacific depending on daylight savings)
sed 's/-08:00//g' /home/pi/multiloop/cgm/cgm-glucose.json | sed 's/-07:00//g' > /home/pi/multiloop/cgm/localized-cgm-glucose.json
# invoke the pebble.json report
openaps report invoke upload/pebble.json
# do some more hacks to make it work
sed 's/content/message/g' /home/pi/multiloop/upload/pebble.json > /home/pi/multiloop/urchin-status.json
# make sure we have clock time
openaps report invoke monitor/dex-clock.json
# format that urchin data
openaps report invoke urchin-data.json
# send it to the watch
openaps use pbl send_urchin_data urchin-data.json
````


````
#!/bin/bash
# pebble-watchface-update.sh - fires on reboot...runs forever? why did I do this?
while true
do
	cd /home/pi/multiloop
  # take whatever data we had last formatted and send to the watch so we know right away we have a good connection
	openaps use pbl send_urchin_data urchin-data.json >/dev/null 2>&1
	sleep 5
done
````

Just for fun, this is what my "upload/pebble.json" report and other items look like from openaps.ini

````
[report "upload/pebble.json"]
suggested = enact/suggested.json
use = shell
temp_basal = monitor/temp_basal.json
reporter = text
basal_profile = settings/basal_profile.json
json_default = True
meal = monitor/meal.json
device = pebble
enacted = enact/enacted.json
remainder = 
iob = monitor/iob.json
glucose = monitor/glucose.json

[vendor "pancreabble"]
path = .
module = pancreabble

[device "pbl"]
vendor = pancreabble
extra = pbl.ini

[device "pebble"]
vendor = openaps.vendors.process
extra = pebble.ini

[report "monitor/dex-clock.json"]
device = cgm
use = ReadDisplayTime
reporter = JSON

[report "urchin-data.json"]
use = format_urchin_data
reporter = JSON
cgm_clock = monitor/dex-clock.json
report = urchin-data.json
device = pbl
glucose_history = cgm/localized-cgm-glucose.json
status_text = 
status_json = urchin-status.json
action = add

````


## Setting the Pebble clock

It's a good idea to set the Pebble clock to match the Pi/Edison once per loop:
```
openaps use pbl set_time
```

## Seemingly correct setup instructions for Raspberry Pi / Edison

1. Install [BlueZ](http://www.bluez.org/) and [libpebble2](https://github.com/pebble/libpebble2).  You need a bluetooth version 5.37 or above.  Best way to install would be:

````
# this installs bluez 5.44
killall bluetoothd &>/dev/null
sudo apt-get update
sudo apt-get install -y libusb-dev libdbus-1-dev libglib2.0-dev libudev-dev libical-dev libreadline-dev --fix-missing
cd $HOME/src/ && wget https://www.kernel.org/pub/linux/bluetooth/bluez-5.44.tar.gz && tar xvfz bluez-5.44.tar.gz || die "Couldn't download bluez"
cd $HOME/src/bluez-5.44 && ./configure --enable-experimental --disable-systemd &&  make && sudo make install && sudo cp ./src/bluetoothd /usr/local/bin/ || die "Couldn't make bluez"

# this installs libpebble2
sudo pip install libpebble2

#reboot the computer to make sure the correct bluetoothd is loaded...I needed to
sudo reboot
````
   
You can confirm your bluetooth version via this command: `bluetoothd --version`

1. Open Settings -> Bluetooth on your Pebble, unpair any phones, and leave it on that screen.

1. Initialize Bluetooth, find the Pebble's Bluetooth MAC address, pair to it, bind it to a virtual serial device.  Get your Pebble's MAC address from the watch Settings --> System -->Information --> BT Address:

  ```
  hciconfig # it's down
  sudo hciconfig hci0 up
  hciconfig # it's up

  systemctl status bluetooth.service # it's inactive
  sudo systemctl start bluetooth.service
  systemctl status bluetooth.service # it's active

  sudo bluetoothctl
  [bluetooth]# scan on
  # ^ find Pebble's MAC address, then you may have to try these a few times:
  [bluetooth]# trust <mac address>
  [bluetooth]# pair <mac address>

  sudo rfcomm bind hci0 <mac address>
  ```

1. Install Pancreabble, add it as an OpenAPS vendor, add a device:

  ```
  pip install --user git+git://github.com/mddub/pancreabble.git

  # in your openaps directory:
  openaps vendor add pancreabble
  openaps device add pbl pancreabble /dev/rfcomm0
  openaps use pbl notify "hello" "testing"

  # result:
  {
    "subject": "hello",
    "message": "testing",
    "received": true
  }
  ```

1. Add these lines to `/etc/rc.local` so that Bluetooth is initialized and the Pebble is paired and bound to `/dev/rfcomm0` on boot:
  ```
  hciconfig hci0 up
  systemctl start bluetooth.service
  rfcomm bind hci0 <mac address>
  ```

## Caveats

* When your Pi/Edison is off the grid and thus doesn't have access to NTP, unless you've [cleverly worked around](https://github.com/openaps/oref0/blob/master/bin/clockset.sh) the Pi's lack of RTC or configured the Edison's RTC, the times reported by that device will also be wrong. (If you do manage to [configure the Edison's RTC](https://communities.intel.com/thread/55831?start=0&tstart=0), would you be so kind as file an issue explaining how you did it?)

## Coming soon

* Package for PyPI
* Auto-configure/pair/bind

# pancreabble

Send OpenAPS status updates to a Pebble watch.

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

## Check out this photo

It doesn't do much yet, but you can send a Pebble "notification" at the end of your loop. Take off the watch band and whoa you just added an e-ink screen to your APS:

![](http://i.imgur.com/wrBmlQM.jpg)

## Temporary, possibly wrong instructions for Raspberry Pi

1. Install [BlueZ](http://www.bluez.org/) and [libpebble2](https://github.com/pebble/libpebble2).

   ```
   # I assume it's something like:
   sudo apt-get install bluez
   sudo pip install libpebble2
   ```

1. Open Settings -> Bluetooth on your Pebble, unpair any phones, and leave it on that screen.

1. Initialize Bluetooth, find the Pebble's Bluetooth MAC address, pair to it, bind it to a virtual serial device:

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
  openaps device add pebble pancreabble /dev/rfcomm0
  openaps use pebble notify "hi" "hello"

  # result:
  {
    "received": true,
    "message": "hello",
    "subject": "hi"
  }
  ```

1. Add these lines to `/etc/rf.local` so that Bluetooth is initialized and the Pebble is paired and bound to `/dev/rfcomm0` on boot:
  ```
  hciconfig hci0 up
  systemctl start bluetooth.service
  rfcomm bind hci0 <mac address>
  ```

## Caveats

* The Pebble expects to have its time set by a [special message](https://libpebble2.readthedocs.org/en/latest/protocol/#fields) from the Pebble app which it expects is running on the smartphone with which it expects to be paired. This library does not currently send that message, so your Pebble's time may be wrong.
* When your Pi/Edison is off the grid and thus doesn't have access to NTP, unless you've [cleverly worked around](https://github.com/openaps/oref0/blob/master/bin/clockset.sh) the Pi's lack of RTC or configured the Edison's RTC, the times reported by that device will also be wrong. (If you do manage to [configure the Edison's RTC](https://communities.intel.com/thread/55831?start=0&tstart=0), would you be so kind as file an issue explaining how you did it?)

## Coming soon

* Clock set command
* Package for PyPI
* Auto-configure/pair/bind
* Support for [Urchin](https://github.com/mddub/urchin-cgm/)

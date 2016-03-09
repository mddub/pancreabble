# pancreabble

Send OpenAPS status updates to a Pebble watch.

Don't use this yet.

### Temporary, possibly wrong instructions for Raspberry Pi:

1. Install [BlueZ](http://www.bluez.org/) and [libpebble2](https://github.com/pebble/libpebble2)

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

1. Add OpenAPS vendor and device:

  ```
  openaps vendor add pancreabble --path /path/to/this/repository
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

### Coming soon

* Package for PyPI
* Auto-configure/pair/bind
* Support for [Urchin](https://github.com/mddub/urchin-cgm/)

import time
from datetime import datetime

import tzlocal
from libpebble2.communication import PebbleConnection
from libpebble2.communication.transports.serial import SerialTransport
from libpebble2.exceptions import TimeoutError
from libpebble2.protocol import SetUTC
from libpebble2.protocol import TimeMessage
from openaps.uses.use import Use


MAX_FAILS = 2
SLEEP_LENGTH = 0.2


class PebbleUse(Use):
    def perform(self, pebble, args, app):
        raise NotImplementedError

    def main(self, args, app):
        port = self.device.get('port')
        fails = 0
        while True:
            try:
                pebble = PebbleConnection(SerialTransport(port))
                pebble.connect()
                pebble.run_async()
                return self.perform(pebble, args, app)
            except TimeoutError:
                fails += 1
                if fails < MAX_FAILS:
                    time.sleep(SLEEP_LENGTH)
                    continue
                else:
                    raise


class set_time(PebbleUse):
    """Set the Pebble time and timezone to match this machine."""
    def perform(self, pebble, args, app):
        localzone = tzlocal.get_localzone()
        pebble.send_packet(
            TimeMessage(message=SetUTC(
                unix_time=time.time(),
                utc_offset=int(localzone.utcoffset(datetime.now()).total_seconds() / 60),
                tz_name=localzone.zone,
            ))
        )
        return {'received': True}

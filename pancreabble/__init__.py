"""
Pancreabble - send OpenAPS status updates to a Pebble watch
"""

import time
from datetime import datetime

import tzlocal
from libpebble2.communication import PebbleConnection
from libpebble2.communication.transports.serial import SerialTransport
from libpebble2.exceptions import TimeoutError
from libpebble2.protocol import SetUTC
from libpebble2.protocol import TimeMessage
from libpebble2.services.notifications import Notifications
from openaps.uses.use import Use

from version import __version__

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


class notify(PebbleUse):
    """Send a push notification, using command line arguments for subject and message."""
    def get_params(self, args):
        return {key: args.__dict__.get(key, '') for key in ('subject', 'message')}

    def configure_app(self, app, parser):
        parser.add_argument('subject')
        parser.add_argument('message')

    def perform(self, pebble, args, app):
        params = self.get_params(args)
        Notifications(pebble).send_notification(params['subject'], params['message'])
        return {
            'subject': params['subject'],
            'message': params['message'],
            'received': True,
        }


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


def configure_add_app(app, parser):
    parser.add_argument('port')

def set_config(args, device):
    device.add_option('port', args.port)

def display_device(device):
    return ''

def get_uses(device, config):
    return [notify, set_time]

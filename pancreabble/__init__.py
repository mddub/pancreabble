"""
Pancreabble - send OpenAPS status updates to a Pebble watch
"""

import time

from libpebble2.communication import PebbleConnection
from libpebble2.communication.transports.serial import SerialTransport
from libpebble2.exceptions import TimeoutError
from libpebble2.services.notifications import Notifications
from openaps.uses.use import Use

MAX_FAILS = 2
SLEEP_LENGTH = 0.2

class notify(Use):
    def get_params(self, args):
        return {key: args.__dict__.get(key, '') for key in ('subject', 'message')}

    def configure_app(self, app, parser):
        parser.add_argument('subject')
        parser.add_argument('message')

    def main(self, args, app):
        params = self.get_params(args)
        port = self.device.get('port')
        fails = 0
        while True:
            try:
                pebble = PebbleConnection(SerialTransport(port))
                pebble.connect()
                pebble.run_async()
                Notifications(pebble).send_notification(params['subject'], params['message'])
                return {
                    'subject': params['subject'],
                    'message': params['message'],
                    'received': True,
                }
            except TimeoutError:
                fails += 1
                if fails < MAX_FAILS:
                    time.sleep(SLEEP_LENGTH)
                    continue
                else:
                    raise

def configure_add_app(app, parser):
    parser.add_argument('port')

def set_config(args, device):
    device.add_option('port', args.port)

def display_device(device):
    return ''

def get_uses(device, config):
    return [notify]

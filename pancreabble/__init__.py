"""
Pancreabble - send OpenAPS status updates to a Pebble watch
"""

import time

from libpebble2.communication import PebbleConnection
from libpebble2.communication.transports.serial import SerialTransport
from libpebble2.exceptions import TimeoutError
from libpebble2.services.notifications import Notifications
from openaps.uses.use import Use
from openaps.uses.registry import Registry

import  list_pebbles

MAX_FAILS = 2
SLEEP_LENGTH = 0.2

use = Registry( )

@use( )
class scan_pebbles (Use):
    def get_params (self, args):
      return dict(timeout=args.timeout)
    def configure_app (self, app, parser):
      parser.add_argument('--timeout', type=int, default=10)
    def main (self, args, app):
      params = self.get_params(args)
      print "pebbles:", params
      result = list_pebbles.do_list(**params)
      # method = list_pebbles.List(**params)
      # method.run( )
      

@use( )
class configure (Use):
    """
    Configure pebble rfcomm
    """
    def configure_app (self, app, parser):
        default_port = self.device.get('port')
        parser.add_argument('--rfcomm', default=None)
        # parser.add_argument('message')
    def get_params (self, args):
        conf = dict(port=None)
        if args.rfcomm:
          conf.update(port=args.rfcomm)
        return conf
    def main (self, args, app):
      dirty = False
      results = dict(port=self.device.get('port', None))
      if args.rfcomm:
        self.device.extra.add_option('port', args.rfcomm)
        results.update(port=args.rfcomm)
        dirty = True
      if dirty:
        self.device.store(app.config)
        app.config.save( )
      return results

@use( )
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
    parser.add_argument('port', nargs='?')


def set_config(args, device):
    port = args.port
    if port:
      device.add_option('port', port)

def display_device(device):
    return ''

get_uses = use.get_uses

from version import VERSION
__version__ = VERSION


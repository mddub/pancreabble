"""
Pancreabble - send OpenAPS status updates to a Pebble watch
"""

from datetime import datetime

from notify import notify
from pebble import set_time
from version import __version__

def configure_add_app(app, parser):
    parser.add_argument('port')

def set_config(args, device):
    device.add_option('port', args.port)

def display_device(device):
    return ''

def get_uses(device, config):
    return [
        notify,
        set_time,
    ]

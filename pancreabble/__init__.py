"""
Pancreabble - send OpenAPS status updates to a Pebble watch
"""

from datetime import datetime

from openaps.uses.use import Use

from notify import notify
from pebble import set_time
from urchin import format_urchin_data
from urchin import send_urchin_data
from handle_notification import handle_notification
from version import __version__

class version(Use):
    """Return the installed version of the Pancreabble library."""
    def main(self, args, app):
        return __version__

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
        format_urchin_data,
        send_urchin_data,
        version,
        handle_notification
    ]

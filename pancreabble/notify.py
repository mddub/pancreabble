from libpebble2.services.notifications import Notifications

from pebble import PebbleUse

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

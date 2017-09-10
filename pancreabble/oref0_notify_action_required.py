from libpebble2.services.notifications import Notifications
from pebble import PebbleUse
import os.path
import time
import json
import string

class oref0_notify_action_required(PebbleUse):
    """Send a push notification if necessary """
    def get_params(self, args):
        return {key: args.__dict__.get(key, '') for key in ('last_notification_file', 'smb_suggested_file', 'snooze')}

    def configure_app(self, app, parser):
        parser.add_argument('last_notification_file')
        parser.add_argument('smb_suggested_file')
        parser.add_argument('snooze')

    def perform(self, pebble, args, app):
        received=False
        subject=""
        message=""
        params = self.get_params(args)
        if os.path.isfile(params['last_notification_file']):
            last_notification=os.path.getmtime(params['last_notification_file'])
            if (time.time()-last_notification)<int(params['snooze'])*60:
                subject="ALREADY_NOTIFIED"
                message="Skipping notification. Last pebble notification sent less than %d minutes ago" % int(params['snooze'])
                received=False

        smb_suggested_file=params['smb_suggested_file']
        if subject=="" and os.path.isfile(smb_suggested_file):
            last_smb_suggested=os.path.getmtime(smb_suggested_file)
            if (time.time()-last_smb_suggested)>int(params['snooze'])*60:
                subject="SMB_SUG_OUT_OF_DATE"
                message="%s not modified for %d minutes" % (smb_suggested_file, int(params['snooze']))
                received=False

        options=json.load(open("pancreoptions.json", "r"))
        options.setdefault('notify_insulinreq', False)
        options.setdefault('notify_carbsreq', False)
        parsesuggested=options['notify_insulinreq'] or options['notify_carbsreq']

        if subject=="" and os.path.isfile(smb_suggested_file) and parsesuggested:
           j=json.load(open(smb_suggested_file, 'r'))
           reason=j.get('reason', '')
           if ("add'l" in reason) or ("maxBolus" in reason):
               bg=j.get('bg', '???')
               tick=j.get('tick', '???')
               carbsReq=j.get('carbsReq', 0.0)
               insulinReq=j.get('insulinReq', 0.0)
               if insulinReq>0:
                  subject="insulinReq"
                  message+="insulinReq: %s. " % insulinReq
               if carbsReq>0:
                  subject="carbsReq"
                  message+="carbsReq: %s. " % carbsReq
               message+=reason
               message+=". BG: %s. Tick: %s." % (bg, tick)
               if (carbsReq>0 and options['notify_carbsreq']) or (insulinReq>0 and options['notify_insulinreq']):
                   Notifications(pebble).send_notification(subject, message)
                   received=True
                   with open(params['last_notification_file'], 'w') as f:
                        f.write(message)
           else:
             subject="OK"
             message="No additional carbs or bolus required."
             received=False
        
        return {
            'subject': subject,
            'message': message,
            'received': received,
        }

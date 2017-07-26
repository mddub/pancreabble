from libpebble2.services.notifications import Notifications
from pebble import PebbleUse
import os.path
import time
import json
import string

SMB_SUGGESTED="enact/smb-suggested.json"

class handle_notification(PebbleUse):
    """Send a push notification if necessary """
    def get_params(self, args):
        return {key: args.__dict__.get(key, '') for key in ('last_notification_file', 'snooze')}

    def configure_app(self, app, parser):
        parser.add_argument('last_notification_file')
        parser.add_argument('snooze')

    def perform(self, pebble, args, app):
        received=False
        subject=""
        message=""
        ret=None
        params = self.get_params(args)
        if os.path.isfile(params['last_notification_file']):
            last_notification=os.path.getmtime(params['last_notification_file'])
            if (time.time()-last_notification)<int(params['snooze'])*60:
                subject="ALREADY_NOTIFIED"
                message="Skipping notification. Last pebble notification sent less than %d minutes ago" % int(params['snooze'])
                received=False
                
        if subject=="" and os.path.isfile(SMB_SUGGESTED):
            last_smb_suggested=os.path.getmtime(SMB_SUGGESTED)
            if (time.time()-last_smb_suggested)>int(params['snooze'])*60:
                subject="SMB_SUG_OUT_OF_DATE"
                message="%s not modified for %d minutes" % (SMB_SUGGESTED, int(params['snooze']))
                received=False

        options=json.load(open("pancreoptions.json", "r"))
        options.setdefault('notify_insulinreq', 'true')
        options.setdefault('notify_carbsreq', 'true')
        options['notify_insulinreq']=string.lower(options['notify_insulinreq'])
        options['notify_carbsreq']=string.lower(options['notify_carbsreq'])
        parsesuggested=options['notify_insulinreq']=='true' or options['notify_carbsreq']=='true'

        if subject=="" and os.path.isfile(SMB_SUGGESTED) and parsesuggested:
           j=json.load(open(SMB_SUGGESTED, 'r'))
           j.setdefault('reason', '')
           reason=j['reason'] 
           if ("add'l" in reason) or ("maxBolus" in reason):
               j.setdefault('bg', '???')
               bg=j['bg']
               j.setdefault('tick', '???')
               tick=j['tick']
               j.setdefault('carbsReq', 0.0)
               j.setdefault('insulinReq', 0.0)
               carbsReq=j['carbsReq']
               insulinReq=j['insulinReq']
               if carbsReq>0:
                  subject="carbsReq"
                  message+="carbsReq: %s. " % carbsReq
               if insulinReq>0:
                  subject="insulinReq"
                  message+="insulinReq: %s. " % insulinReq
               message+=reason
               message+=". BG: %s. Tick: %s." % (bg, tick)
               if (carbsReq>0 and options['notify_carbsreq']=='true') or (insulinReq>0 and options['notify_insulinreq']=='true'):
                   Notifications(pebble).send_notification(subject, message)
                   received=True
                   f=open(params['last_notification_file'], "w")
                   f.write(message)
                   f.close()
           else:
             subject="OK"
             message="No additional carbs or bolus required."
             received=False
        
        return {
            'subject': subject,
            'message': message,
            'received': received,
        }

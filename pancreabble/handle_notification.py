from libpebble2.services.notifications import Notifications
from pebble import PebbleUse
import os.path
import time

SMB_SUGGESTED="enact/smb-suggested.json"

class handle_notification(PebbleUse):
    """Send a push notification if necessary """
    def get_params(self, args):
        return {key: args.__dict__.get(key, '') for key in ('last_notification_file', 'snooze')}

    def configure_app(self, app, parser):
        parser.add_argument('last_notification_file')
        parser.add_argument('snooze')

    def dict_get(d, k):
        if d.has_key(k):
            return d[k]
        else
            return ""

    def perform(self, pebble, args, app):
        received=False
        subject=""
        message=""
        ret=None
        params = self.get_params(args)
        if os.path.isfile(params['last_notification_file']):
            last_notification=os.path.getmtime(params['last_notification_file']))
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

        if subject=="" and os.path.isfile(SMB_SUGGESTED):
           j=json.load(SMB_SUGGESTED)
           reason=dict_get(j, 'reason')
           if ("add'l" in reason) or ("maxBolus" in reason):
               bg=dict_get(j, 'bg')
               tick=dict_get(j, 'tick')
               carbsReq=dict_get(j, 'carbsReq')
               insulinReq=dict_get(j, 'insulinReq')
               if int(carbsReq)>0:
                  subject="carbsReq"
                  message+="carbsReq: %s. " % carbsReq
               if int(insulinReq)>0:
                  subject="insulinReq"
                  message+="insulinReq: %s. " % insulinReq
               message+=reason
               message+=". BG: %s. Tick: %s." % (bg, tick)
               Notifications(pebble).send_notification(subject, message)
               received=True
               f=open(params['last_notification_file'], "w")
               f.write(message)
               f.close()
           else
             subject="OK"
             message="No additional carbs or bolus required."
             received=False
        
        return {
            'subject': subject,
            'message': message,
            'received': received,
        }

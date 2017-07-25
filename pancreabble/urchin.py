import json
import os
import time
import dateutil.parser
from datetime import datetime
from datetime import timedelta
from operator import itemgetter
from uuid import UUID

from libpebble2.services.appmessage import AppMessageService
from libpebble2.services.appmessage import ByteArray
from libpebble2.services.appmessage import CString
from libpebble2.services.appmessage import Int32
from openaps.uses.use import Use

from pebble import PebbleUse

URCHIN_UUID = UUID('ea361603-0373-4865-9824-8f52c65c6e07')
MAX_URCHIN_SGVS = 144
NO_DELTA_VALUE = 65536

DEXCOM_TRENDS = [
    None,
    'DOUBLE_UP',
    'SINGLE_UP',
    '45_UP',
    'FLAT',
    '45_DOWN',
    'SINGLE_DOWN',
    'DOUBLE_DOWN',
    'NOT_COMPUTABLE',
    'OUT_OF_RANGE'
]

APP_KEYS = [
    'msgType',
    'recency',
    'sgvCount',
    'sgvs',
    'lastSgv',
    'trend',
    'delta',
    'statusText',
    'graphExtra',
]

def to_byte_array(arr):
    return ByteArray(''.join(map(chr, arr)))

TYPE_CAST = {
    # PebbleKit JS on iOS/Android casts any number to int32. May as well follow that here.
    'msgType': Int32,
    'recency': Int32,
    'sgvCount': Int32,
    'sgvs': to_byte_array,
    'lastSgv': Int32,
    'trend': Int32,
    'delta': Int32,
    'statusText': CString,
    'graphExtra': to_byte_array,
}

def graph_array(end_time, sgvs, count):
    # Reimplementation of https://github.com/mddub/urchin-cgm/blob/2736df/src/js/format.js#L7-L44
    INFINITY = timedelta(days=999999)
    no_entry = {
        'date': datetime.now() + INFINITY,
        'sgv': 0,
    }

    graphed = [no_entry] * count
    xs = [end_time - timedelta(minutes=m) for m in range(0, 5 * count, 5)]

    for sgv in sgvs:
        min_distance = INFINITY
        # Don't graph missing sgvs or error codes
        if sgv['sgv'] is None or sgv['sgv'] <= 12:
            continue
        # Find the x value closest to this sgv's date
        xi = None
        for j, x in enumerate(xs):
            if abs(sgv['date'] - x) < min_distance:
                min_distance = abs(sgv['date'] - x)
                xi = j
        # Assign it if it's the closest sgv to that x
        if min_distance < timedelta(minutes=5) and abs(sgv['date'] - xs[xi]) < abs(graphed[xi]['date'] - xs[xi]):
            graphed[xi] = sgv

    return [g['sgv'] for g in graphed]


class format_urchin_data(Use):
    """Format CGM history as a message for the Urchin watchface."""
    def configure_app(self, app, parser):
        parser.add_argument(
            'glucose_history',
            help='JSON file containing glucose history',
            metavar='glucose-history.json'
        )
        parser.add_argument(
            '--cgm-clock',
            help='JSON file containing the display time of the CGM (e.g. from ReadDisplayTime use for Dexcom). Optional, but highly recommended for accurate reporting of CGM recency.',
            metavar='cgm-clock.json',
            required=False
        )
        parser.add_argument(
            '--status-text',
            help='A string to be displayed in the status line',
            metavar='STRING',
            required=False
        )
        parser.add_argument(
            '--status-json',
            help='JSON file with a "message" key containing a string to be displayed in the status line',
            metavar='urchin-status.json',
            required=False
        )

    def to_ini(self, args):
        # XXX: openaps really should be smarter about serializing None
        return dict((k, v or '') for k, v in args.__dict__.iteritems())

    def main(self, args, app):
        cgm_history = json.loads(open(args.glucose_history).read())
        cgm_records = [
            {
                #'date': datetime.strptime(r['display_time'], '%Y-%m-%dT%H:%M:%S'),
                'date': dateutil.parser.parse(r['display_time'], ignoretz=True),
                'sgv': r['glucose'],
                'trend': DEXCOM_TRENDS.index(r.get('trend_arrow')),
            }
            for r
            in sorted(cgm_history, key=itemgetter('display_time'), reverse=True)
        ]
        end_time = cgm_records[0]['date']
        graph = graph_array(end_time, cgm_records, MAX_URCHIN_SGVS)
        delta = NO_DELTA_VALUE if graph[1] == 0 else (graph[0] - graph[1])

        if args.cgm_clock:
            cgm_clock = datetime.strptime(json.loads(open(args.cgm_clock).read()), '%Y-%m-%dT%H:%M:%S')
            cgm_clock_reported_at = datetime.fromtimestamp(os.stat(args.cgm_clock).st_mtime)
            recency = int((datetime.now() - end_time + cgm_clock - cgm_clock_reported_at).total_seconds())
        else:
            # Without knowing offset of device clock, just use mtime of CGM history file
            recency = int(time.time() - os.stat(args.glucose_history).st_mtime)

        status = 'openaps @ {:%-I:%M%P}'.format(datetime.now())
        if args.status_text:
            status = arg
            s.status_text
        elif args.status_json:
            status = json.loads(open(args.status_json).read())['message']

        # TODO: format pump bolus/basal history
        #   https://github.com/mddub/urchin-cgm/blob/6c3833/src/js/data.js#L681-L716
        #   https://github.com/mddub/urchin-cgm/blob/2736df/src/js/format.js#L57-L133
        graph_extra = [0] * len(graph)

        return {
            'msgType': 1,
            'recency': recency,
            'sgvCount': len(graph),
            'sgvs': [y / 2 for y in graph],
            'lastSgv': graph[0],
            'trend': cgm_records[0]['trend'],
            'delta': delta,
            'statusText': status,
            'graphExtra': graph_extra,
        }


class send_urchin_data(PebbleUse):
    """Send formatted CGM and pump history (from format_urchin_data) to the Urchin watchface."""
    def configure_app(self, app, parser):
        parser.add_argument('formatted_data', metavar='formatted_data.json')

    def perform(self, pebble, args, app):
        json_message = json.loads(open(args.formatted_data).read())
        app_message = dict(
            (i, TYPE_CAST[key](json_message[key]))
            for i, key
            in enumerate(APP_KEYS)
        )
        AppMessageService(pebble).send_message(URCHIN_UUID, app_message)
        return {'received': True}



import pydbus
from gi.repository import Gio, GLib, GObject

from threading import Thread, Event

class ifaces:
  Introspectable = 'org.freedesktop.DBUS.Introspectable'
  ObjectManager = 'org.freedesktop.DBUS.ObjectManager'
  Properties = 'org.freedesktop.DBUS.Properties'
  BLUEZ = 'org.bluez'
  Adapter1 = 'org.bluez.Adapter1'
  Device1 = 'org.bluez.Device1'

class App (object):
  def __init__ (self, timeout):
    GObject.threads_init( )
    self.timeout = timeout
    self.loop = GLib.MainLoop( )
    self.ev = Event( )


  def run (self):
    self.thread = Thread(target=self.pending)
    self.thread.daemon = True
    self.thread.start( )
    self.loop.run( )
  def pending (self):
    self.ev.wait(self.timeout)
    self.loop.quit( )
    print "done"
    self.expired( )
  def prelude (self):
    pass
  def expired (self):
    pass

def on_change (*args):
  print 'changed', args

def do_list (timeout=None, **kwds):
  app = List(timeout)
  with pydbus.SystemBus( ) as bus:
    adapter = bus.get(ifaces.BLUEZ, '/org/bluez/hci0')
    adapter.PropertiesChanged.connect(on_change)
    root = bus.get(ifaces.BLUEZ, '/')
    root.InterfacesAdded.connect(app.changed_iface)
    root.InterfacesRemoved.connect(app.changed_iface)
    bluez = bus.get(ifaces.BLUEZ, '/org/bluez')
    managed = root.GetManagedObjects( )

    for path, spec in managed[0].items():
      print path
      if ifaces.Device1 in spec:
        print spec
        props = spec.get(ifaces.Device1, {})
        print "FOUND", path, props.get('Alias', ''), props.get('Address', ''), props.get('RSSI', '')
    adapter.StartDiscovery( )
    print "adapater", adapter
    # help(bluez)
    app.run( )
    adapter.StopDiscovery( )


class List (App):
  def changed_iface (self, path, prop_spec):
    props = prop_spec.get(ifaces.Device1, {})
    print "ADDED", path, props.get('Alias', ''), props.get('Address', ''), props.get('RSSI', '')
  def expired (self):
    print "done"


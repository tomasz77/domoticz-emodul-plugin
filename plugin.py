# Domoticz Emodul Plugin
#
# Author: Tomasz Jagiełło <jagiello.tomek@gmail.com>
#
"""
<plugin key="emodul" name="EMODUL" author="Tomasz Jagiello" version="0.0.1" wikilink="" externallink="https://github.com/tomasz77/domoticz-emodul-plugin.git">
    <description>
        <h2>EMODUL Plugin v.0.0.1</h2><br/>
        Supports only temperature sensors (zones)<br/>
        Just enter your username and password for the App used and temperature sensors will be detected automatically.
    </description>
    <params>
        <param field="Username" label="App Username" width="300px" required="true" default=""/>
        <param field="Password" label="App Password" width="300px" required="true" default="" password="true"/>
    </params>
</plugin>
"""
try:
    import Domoticz
except ImportError:
    #import fake domoticz modules and setup fake domoticz instance to enable unit testing
    from fakeDomoticz import *
    from fakeDomoticz import Domoticz
    Domoticz = Domoticz()
import json
import sys
import threading
import time
import urllib.request


class BasePlugin:
    token = None
    user_id = None
    startup = True
    devs = []
    last_update = 0

    def __init__(self):
        self.base_url = "https://emodul.eu/api/v1"
        self.token = None
        self.user_id = None
        return

    def authenticate(self, username, password):
        auth_url = f"{self.base_url}/authentication"
        data = {"username": username, "password": password}
        headers = {"Content-Type": "application/json"}
        request = urllib.request.Request(auth_url, data=json.dumps(data).encode(), headers=headers)
        try:
            with urllib.request.urlopen(request) as response:
                auth_data = json.loads(response.read().decode())
                self.token = auth_data["token"]
                self.user_id = auth_data["user_id"]
                Domoticz.Debug("Authentication successful.")
        except urllib.error.URLError as e:
            Domoticz.Error(f"Authentication failed: {e.reason}")

    def onStart(self):
        self.updateThread = threading.Thread(name="EmodulUpdateThread", target=BasePlugin.handleThread, args=(self,))
        self.updateThread.start()

    def onStop(self):
        Domoticz.Debug("onStop called")
        while (threading.active_count() > 1):
            time.sleep(1.0)

    def onConnect(self, Connection, Status, Description):
        Domoticz.Debug("onConnect called")

    def onMessage(self, Connection, Data):
        Domoticz.Debug("onMessage called")

    def onCommand(self, Unit, Command, Level, Hue):
        Domoticz.Debug("onCommand called for Unit " + str(Unit) + ": Parameter '" + str(Command) + "', Level: " + str(Level))

    def onNotification(self, Name, Subject, Text, Status, Priority, Sound, ImageFile):
        Domoticz.Debug("Notification: " + Name + "," + Subject + "," + Text + "," + Status + "," + str(Priority) + "," + Sound + "," + ImageFile)

    def onDisconnect(self, Connection):
        Domoticz.Debug("onDisconnect called")

    def onHeartbeat(self):
        # If it hasn't been at least 1 minute since last update, skip it
        if time.time() - self.last_update < 61:
            return
        Domoticz.Debug("onHeartbeat called time="+str(time.time()))
        # Create/Start update thread
        self.updateThread = threading.Thread(name="EmodulUpdateThread", target=BasePlugin.handleThread, args=(self,))
        self.updateThread.start()

    def get_modules(self):
        modules_url = f"{self.base_url}/users/{self.user_id}/modules"
        headers = {"Authorization": f"Bearer {self.token}"}
        request = urllib.request.Request(modules_url, headers=headers)
        try:
            with urllib.request.urlopen(request) as response:
                if response.status == 200:
                    modules_data = json.loads(response.read().decode())
                    return modules_data
                else:
                    Domoticz.Log("Failed to retrieve module data.")
        except urllib.error.URLError as e:
            Domoticz.Log(f"Failed to retrieve module data: {e.reason}")

    def get_module_data(self, module_udid):
        module_url = f"{self.base_url}/users/{self.user_id}/modules/{module_udid}"
        headers = {"Authorization": f"Bearer {self.token}"}
        request = urllib.request.Request(module_url, headers=headers)
        try:
            with urllib.request.urlopen(request) as response:
                if response.status == 200:
                    module_data = json.loads(response.read().decode())
                    return module_data
                else:
                    Domoticz.Log(f"Failed to retrieve data for module {module_udid}.")
        except urllib.error.URLError as e:
            Domoticz.Log(f"Failed to retrieve data for module {module_udid}: {e.reason}")

    def get_devices(self):
        modules = self.get_modules()
        devices = []
        if modules:
            for module in modules:
                module_udid = module["udid"]
                module_data = self.get_module_data(module_udid)
                if module_data:
                    for dev_data in module_data.get("zones", {}).get("elements", {}):
                        battery_level = dev_data.get("zone", {}).get("batteryLevel", 0)
                        if battery_level != 0:
                            devices.extend([{
                                "id": "emodul_zone_{}".format(dev_data["zone"]["id"]),
                                "name": dev_data["description"]["name"],
                                "current_temperature": dev_data["zone"]["currentTemperature"]
                            }])
        return devices

    # Separate thread looping ever 10 seconds searching for new TUYAs on network and updating their status
    def handleThread(self):
        try:
            Domoticz.Debug("in handlethread")
            self.authenticate(Parameters["Username"], Parameters["Password"])

            self.devs = self.get_devices()

            # Set last update
            self.last_update = time.time()

            # Update devices
            for dev in self.devs:
                unit = getUnit(dev["id"])
                if unit == 0:
                    unit = nextUnit()
                    Domoticz.Device(Name=dev["name"], Unit=unit, TypeName="Temperature", Switchtype=-1, DeviceID=str(dev["id"])).Create()
                if dev['current_temperature'] is not None:
                    UpdateDevice(unit, 0, "{}".format(dev['current_temperature']/10), False)

            self.startup = False

        except Exception as err:
            Domoticz.Error("handleThread: "+str(err)+' line '+format(sys.exc_info()[-1].tb_lineno))
            

global _plugin
_plugin = BasePlugin()

def onStart():
    global _plugin
    _plugin.onStart()

def onStop():
    global _plugin
    _plugin.onStop()

def onConnect(Connection, Status, Description):
    global _plugin
    _plugin.onConnect(Connection, Status, Description)

def onMessage(Connection, Data):
    global _plugin
    _plugin.onMessage(Connection, Data)

def onCommand(Unit, Command, Level, Hue):
    global _plugin
    _plugin.onCommand(Unit, Command, Level, Hue)

def onNotification(Name, Subject, Text, Status, Priority, Sound, ImageFile):
    global _plugin
    _plugin.onNotification(Name, Subject, Text, Status, Priority, Sound, ImageFile)

def onDisconnect(Connection):
    global _plugin
    _plugin.onDisconnect(Connection)

def onHeartbeat():
    global _plugin
    _plugin.onHeartbeat()


# Loop thru domoticz devices and see if there's a device with matching DeviceID, if so, return unit number, otherwise return zero
def getUnit(devid):
    unit = 0
    for x in Devices:
        if Devices[x].DeviceID == devid:
            unit = x
            break
    return unit

# Find the smallest unit number available to add a device in domoticz
def nextUnit():
    unit = 1
    while unit in Devices and unit < 255:
        unit = unit + 1
    return unit

def UpdateDevice(Unit, nValue, sValue, TimedOut):
    # Make sure that the Domoticz device still exists (they can be deleted) before updating it
    if Unit in Devices:
        if (Devices[Unit].nValue != nValue) or (Devices[Unit].sValue != sValue) or (Devices[Unit].TimedOut != TimedOut):
            Devices[Unit].Update(nValue=nValue, sValue=sValue, TimedOut=TimedOut)
            Domoticz.Log("Update {}:{} ({}) TimedOut={}".format(nValue, sValue, Devices[Unit].Name, TimedOut))
    return

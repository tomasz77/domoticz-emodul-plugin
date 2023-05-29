import json

#
#   Fake Domoticz - Domoticz Python plugin stub
#
#   With thanks to Frank Fesevur, 2017
#
#   Very simple module to make local testing easier
#   It "emulates" Domoticz.Log(), Domoticz.Error and Domoticz.Debug()
#   It also emulates the Device and Unit from the Ex framework
#
Devices = dict()
Parameters = json.load(open('fakeParameters.json'))
config = dict()


class myUnit:
    def __init__(self, Name="label", Unit=0, Type=0, Subtype=0, Switchtype="", DeviceID="deviceURL", Used=0):
        self.Name = Name
        self.Unit = Unit,
        self.Type = Type
        self.Subtype = Subtype
        self.Switchtype = Switchtype
        self.DeviceID = DeviceID
        self.Used = Used

    def Create(self):
        print("Creating unit " + self.Name + " for deviceID " + self.DeviceID)


class Domoticz:
    def __init__(self):
        self.Units = []
        return

    def Log(self, s):
        print(s)

    def Status(self, s):
        print(s)

    def Error(self, s):
        print(s)

    def Debug(self, s):
        print(s)

    def Debugging(self, level):
        print("debugging set to " + str(level))

    def Heartbeat(self, level):
        print("heartbeat set to " + str(level))

    def Device(self, Name="", Unit=-1, TypeName="", Switchtype=-1, DeviceID=""):
        Devices[Unit] = FakeDevice(DeviceID, Name)
        print("constructing Device: Name={}, Unit={}, TypeName={}, Switchtype={}, DeviceID={}".format(
            Name, Unit, TypeName, Switchtype, DeviceID
        ))
        return Devices[Unit]

    def Unit(self, Name="label", Unit=0, Type=0, Subtype=0, Switchtype="", DeviceID="deviceURL", Used=0):
        newUnit = myUnit(Name, Unit, Type, Subtype, Switchtype, DeviceID, Used)
        # self.Devices[DeviceID].Units.append(newUnit)
        self.Units.append(newUnit)
        return newUnit

    def Configuration(self):
        return config

class FakeDevice:
    DeviceID = None
    Name = None
    nValue = 0
    sValue = ""
    TimedOut = False

    def __init__(self, DeviceID, DeviceName):
        self.DeviceID = DeviceID
        self.Name = DeviceName

    def Create(self):
        print("Creating device {}".format(self.DeviceID))

    def Update(self, nValue=0, sValue="", TimedOut=False):
        print("Updating device {}: nValue={}, sValue={}, TimedOut={}".format(
            self.DeviceID, nValue, sValue, TimedOut
        ))
        self.nValue = nValue
        self.sValue = sValue
        self.TimedOut = TimedOut


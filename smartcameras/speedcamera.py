import uuid
import datetime
import time
import numpy as np
import threading
import vehicle
import azurehook
import json

class SpeedCamera(object):
    TOPIC_CAMERA = "SpeedCamera"
    TOPIC_VEHICLE = "Vehicle"
    FILTER_CAMERA_ACTIVATED = "Activated"
    FILTER_CAMERA_DEACTIVATED = "Deactivated"

    def __init__(self, street, city, cloudhook = None, name = None):
        self.id = str(uuid.uuid4())
        self.street = street
        self.city = city
        self.isActive = False
        self.speedLimit = None
        self.rate = None
        if cloudhook is None:
            self.cloudhook = azurehook.AzureHook()
        if name is not None:
            self.name = name

    def relocate(self, street, city = None):
        self.street = street
        if(city is not None):
            self.city = city

    # Most commonly executes on its own thread
    def activate(self, speedLimit, rate):
        if(self.isActive is True):
            raise EnvironmentError('Speed camera is already active: deactivate first.')
        self.speedLimit = speedLimit
        self.rate = rate
        self.datetime = datetime.datetime.now()
        self.isActive = True
        # Inform Azure of activated camera
        self.__notifyCloudOfSelf()
        # Event representing the passing of the next vehicle
        self.nextVehicle = threading.Event()
        # Loop until deactivate is called
        # (preferably from a separate thread/process!!!!)
        while self.isActive:
            nextArrival = self.__genNextArrival()
            self.nextVehicle.wait(timeout=nextArrival)
            # Vehicle has passed - Create new vehicle
            self.__onObservedVehicle()
        # End of Loop

    # Preferably called from a separate thread
    def deactivate(self):
        self.isActive = False
        self.nextVehicle.set()

    def toJson(self):
        return json.dumps({"id"         : self.id,
                           "street"     : self.street,
                           "city"       : self.city,
                           "rate"       : self.rate,
                           "speedLimit" : self.speedLimit,
                           "isActive"   : self.isActive,
                           "last_activation" : str(self.datetime)},
                           indent = 4, sort_keys = True)

    ## Helping/Private methods
    ################################################
    def __genNextArrival(self):
        if(self.rate is None):
            raise ValueError("Rate is undefined")
        return np.random.exponential(1./self.rate)

    def __notifyCloudOfSelf(self):
        pass
        self.cloudhook.createTopic(self.TOPIC_CAMERA)
        self.cloudhook.publish(self.TOPIC_CAMERA, self.toJson())

    def __notifyCloudOfVehicle(self, vehicle):
        pass
        self.cloudhook.createTopic(self.TOPIC_CAMERA)
        self.cloudhook.publish(self.TOPIC_CAMERA, vehicle.toJson())

    def __onObservedVehicle(self):
        # print "Woooooooooooooo -  A new vehicle just passed by"
        aVehicle = vehicle.NormalVehicle(self.speedLimit)
        self.__notifyCloudOfVehicle(aVehicle)


# def cameraFromJson(json_string):
#     return json.loads(json_string, object_hook=asSpeedCamera)
#
# def asSpeedCamera(dic):
#     SpeedCamera = SpeedCamera(dic['street'], dic['city'])
#     vehicle.__dict__.update(dic)
#     return vehicle

# def main():
#     parser = argparse.ArgumentParser(
#         description='Launch a speed camera')
#     parser.add_argument('action',
#                         metavar="<action>",
#                         choices=['start', 'shutdown', 'status', 'camera'],
#                         help='%(choices)s')
#
# if __name__ == "__main__":
#     main()

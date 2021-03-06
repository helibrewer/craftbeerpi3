# -*- coding: utf-8 -*-
import os
from subprocess import Popen, PIPE, call

from modules import cbpi, app
from modules.core.hardware import SensorPassive
import json
import os, re, threading, time
from flask import Blueprint, render_template, request
from modules.core.props import Property

blueprint = Blueprint('one_wire', __name__)

temp = 22

def getSensors():
    try:
        arr = []
        for dirname in os.listdir('/sys/bus/w1/devices'):
            if (dirname.startswith("28") or dirname.startswith("10")):
                arr.append(dirname)
        return arr
    except:
        return []




class myThread (threading.Thread):

    value = 0


    def __init__(self, sensor_name):
        threading.Thread.__init__(self)
        self.value = 0
        self.sensor_name = sensor_name
        self.runnig = True

    def shutdown(self):
        pass

    def stop(self):
        self.runnig = False

    def run(self):

        while self.runnig:
            try:
                app.logger.info("READ TEMP")
                ## Test Mode
                if self.sensor_name is None:
                    return
                with open('/sys/bus/w1/devices/w1_bus_master1/%s/w1_slave' % self.sensor_name, 'r') as content_file:
                    content = content_file.read()
                    if (content.split('\n')[0].split(' ')[11] == "YES"):
                        temp = float(content.split("=")[-1]) / 1000  # temp in Celcius
                        self.value = temp
            except:
                pass

            time.sleep(4)



@cbpi.sensor
class ONE_WIRE_SENSOR(SensorPassive):

    sensor_name = Property.Select("Sensor", getSensors())
    offset = Property.Number("Offset", True, 0)

    def init(self):

        self.t = myThread(self.sensor_name)

        def shudown():
            shudown.cb.shutdown()
        shudown.cb = self.t

        self.t.start()

    def stop(self):
        try:
            self.t.stop()
        except:
            pass

    def read(self):
        if self.get_config_parameter("unit", "C") == "C":
            self.data_received(round(self.t.value + float(self.offset), 2))
        else:
            self.data_received(round(9.0 / 5.0 * self.t.value + 32 + float(self.offset), 2))

    @classmethod
    def init_global(self):
        try:
            call(["modprobe", "w1-gpio"])
            call(["modprobe", "w1-therm"])
        except Exception as e:
            pass


@blueprint.route('/<int:t>', methods=['GET'])
def set_temp(t):
    global temp
    temp = t
    return ('', 204)


@cbpi.initalizer()
def init(cbpi):
    cbpi.app.logger.info("INITIALIZE ONE WIRE MODULE")
    cbpi.app.register_blueprint(blueprint, url_prefix='/api/one_wire')

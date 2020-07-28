from sanic import Sanic, request, Blueprint
from sanic.response import json, text
from datetime import datetime, date, timedelta
import time
import asyncio
from gateway_dock import database, app

gateway = Blueprint('gateway', url_prefix='')

@gateway.route("/dock/stop/<dockCode>", methods=['GET','POST'])
async def dockStop(request, dockCode):
    print(f"[SERVER]                    :   {request.body.decode('utf-8')}")
    # print(database.is_connected)
    data_dock = dict(eval(request.body.decode('utf-8')))
    return text('OK')

@gateway.route("/dock/start/<dockCode>", methods=['GET','POST'])
async def dockStop(request, dockCode):
    print(f"[SERVER]                    :   {request.body.decode('utf-8')}")
    # print(database.is_connected)
    data_dock = dict(eval(request.body.decode('utf-8')))
    return text('OK')

@gateway.route("/dock/booking/<dockCode>", methods=['GET','POST'])
async def dockStop(request, dockCode):
    print(f"[SERVER]                    :   {request.body.decode('utf-8')}")
    # print(database.is_connected)
    data_dock = dict(eval(request.body.decode('utf-8')))
    return text('OK')

@gateway.route("/dock/alarm-stop/<dockCode>", methods=['GET','POST'])
async def dockStop(request, dockCode):
    print(f"[SERVER]                    :   {request.body.decode('utf-8')}")
    # print(database.is_connected)
    data_dock = dict(eval(request.body.decode('utf-8')))
    return text('OK')

@gateway.route("/dock/alarm-start/<num>", methods=['GET','POST'])
async def dockStop(request, dockCode):
    print(f"[SERVER]                    :   {request.body.decode('utf-8')}")
    # print(database.is_connected)
    data_dock = dict(eval(request.body.decode('utf-8')))
    return text('OK')

@gateway.route("/LD/HF/<dockCode>", methods=['GET','POST'])
async def dockIdHF(request, dockCode):
    print(f"[HF READER]                 :   {request.body.decode('utf-8')}")
    dataEPC = request.body.decode('utf-8')
    return text('OK')

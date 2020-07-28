from sanic import Sanic, Blueprint
from databases import Database
import asyncio

class Logger(object):
    def __init__(self):
        self.terminal = sys.stdout
        self.log = open("logfile.log", "a")

    def write(self, message):
        self.terminal.write(message)
        self.log.write(message)

    def flush(self):
        #this flush method is needed for python 3 compatibility.
        #this handles the flush command by doing nothing.
        #you might want to specify some extra behavior here.
        pass

app = Sanic(__name__)
DATABASE_URL = 'mysql://root@localhost:3306/polytama_dev'
database = Database(DATABASE_URL)


@app.listener('after_server_start')
async def setup_db(app, loop):
    await database.connect()

from gateway_dock.views import gateway

gateRoute = Blueprint.group(gateway, url_prefix='')
app.blueprint(gateRoute)

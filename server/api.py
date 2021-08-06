import os

from flask import Flask, jsonify
from flask_restful import Resource, Api

import procrastinot as pnot

app = Flask('procrastiNOT')
app.json_encoder = pnot.ProcNOTJsonEncoder
api = Api(app)

pronot = pnot.ProcrastiNOT('example_config.json')


class Items(Resource):
    """ Returns list fo registered items in the system """

    def get(self):
        return jsonify(pronot.items)


api.add_resource(Items, '/items')


class Status(Resource):
    """ Returns for each item whether it is currently blocked or not """

    def get(self):
        return []


api.add_resource(Status, '/status')


class Start(Resource):
    """ Starts an unscheduled blockade """

    def post(self):
        pass


api.add_resource(Start, '/start')


class Stop(Resource):
    """ Stops current blockade """

    def post(self):
        pass


api.add_resource(Stop, '/stop')


class Schedule(Resource):
    """
    PUT: Adds a schedule
    GET: Get list of schedules
    """

    def put(self):
        pass

    def get(self):
        return jsonify(pronot.blockades)


api.add_resource(Schedule, '/schedule')


class Register(Resource):
    """
    Register to be notified about starting or
    stopping of a blockade contatining any of the given items
    """

    def put(self):
        pass


api.add_resource(Register, '/register')

if __name__ == '__main__':
    app.run(debug=True)

    if not app.debug or os.environ.get('WERKZEUG_RUN_MAIN') == 'true':
        # Make sure this happens only once when Flask is in debug mode
        pronot.init_schedules()

import pprint
from datetime import datetime, timedelta
from functools import wraps
from itertools import count

from flask import Flask, jsonify, request
from flask_cors import CORS
from flask_pydantic import validate

from resource import Position, ClosePosition, ModifyPosition
from service import *
from utils import *

app = Flask(__name__)
CORS(app)


def auth():
    def token_required(f):
        @wraps(f)
        def decorator(*args, **kwargs):
            token = request.headers.get('token')
            if token != getEnvValue("AUTH_TOKEN"):
                return jsonify({'message': 'Authorization exception'}), 401
            return f(*args, **kwargs)

        return decorator

    return token_required


@app.route('/info', methods=['POST'])
@auth()
@validate()
def info():
    result = {}
    try:
        args = request.json
        symbols = args.get("symbols")
        timeframes = args.get("timeframes")
        for symbol in symbols:
            result[symbol] = {}
            count = symbols[symbol]
            for timeframe in timeframes:
                start_pos = timeframes[timeframe]
                service = Metatrader(
                    symbol=symbol,
                    username=int(args.get("username")),
                    password=args.get("password"),
                    server=args.get("server")
                )

                info = service.info(
                    timeframe=timeframe,
                    start_pos=start_pos,
                    count=count
                )
                result[symbol][timeframe] = info

        return jsonify(result), 200
    except Exception as error:
        return jsonify(result), 200


@app.route('/account-info', methods=['POST'])
@auth()
def account_info():
    try:
        args = request.json
        service = Metatrader(
            username=int(args.get("username")),
            password=args.get("password"),
            server=args.get("server")
        )

        info = service.get_account_info()
        if info is None:
            return jsonify({"error": "could not fetch account info, check credentials/connection"}), 502

        return jsonify(info._asdict()), 200
    except Exception as error:
        return jsonify({"error": str(error)}), 500


@app.route('/positions', methods=['POST'])
@auth()
def positions():
    try:
        args = request.json
        service = Metatrader(
            username=int(args.get("username")),
            password=args.get("password"),
            server=args.get("server")
        )

        result = service.get_positions(args.get("symbol"))
        return jsonify(result), 200
    except Exception as error:
        return jsonify({"error": str(error)}), 500


@app.route('/history', methods=['POST'])
@auth()
def history():
    try:
        args = request.json
        service = Metatrader(
            username=int(args.get("username")),
            password=args.get("password"),
            server=args.get("server")
        )

        date_from = datetime.fromisoformat(args["from"]) if args.get("from") else datetime.utcnow() - timedelta(days=30)
        date_to = datetime.fromisoformat(args["to"]) if args.get("to") else datetime.utcnow()

        result = service.get_history(date_from, date_to)
        return jsonify(result), 200
    except Exception as error:
        return jsonify({"error": str(error)}), 500


@app.route('/trade', methods=['POST'])
@auth()
@validate()
def trade(body: Position):
    try:
        service = Metatrader(
            symbol=body.symbol,
            username=int(body.username),
            password=body.password,
            server=body.server
        )

        result = service.trade({
            "symbol": body.symbol,
            "side": body.side,
            "volume": body.volume,
            "sl": body.sl,
            "tp": body.tp,
            "type_time": body.type_time,
            "type_filling": body.type_filling,
            "comment": body.comment,
        })
        return jsonify(result), 200
    except Exception as error:
        return jsonify({"error": str(error)}), 500

@app.route('/close-position', methods=['POST'])
@auth()
@validate()
def close_position(body: ClosePosition):
    try:
        service = Metatrader(
            username=int(body.username),
            password=body.password,
            server=body.server
        )

        result = service.close_position(body.ticket, comment=body.comment)
        return jsonify(result), 200
    except Exception as error:
        return jsonify({"error": str(error)}), 500


@app.route('/modify-position', methods=['POST'])
@auth()
@validate()
def modify_position(body: ModifyPosition):
    try:
        service = Metatrader(
            username=int(body.username),
            password=body.password,
            server=body.server
        )

        result = service.modify_position(body.ticket, sl=body.sl, tp=body.tp)
        return jsonify(result), 200
    except Exception as error:
        return jsonify({"error": str(error)}), 500


if __name__ == '__main__':
    app.run(host="0.0.0.0", port=5000, debug=True)

# src/api/routes.py
from datetime import datetime, timedelta, timezone
from flask import Blueprint, jsonify, request
from flask_pydantic import validate

from src.api.middleware import auth
from src.schemas.payloads import Position, ClosePosition, ModifyPosition
from src.services.mt5_client import MT5Client
from src.utils.logger import logger

api_bp = Blueprint("api", __name__)


@api_bp.route("/info", methods=["POST"])
@auth()
@validate()
def info():
    result = {}
    try:
        args = request.json or {}
        symbols = args.get("symbols", {})
        timeframes = args.get("timeframes", {})

        # Connect once for the whole batch
        service = MT5Client(
            username=int(args.get("username")),
            password=args.get("password"),
            server=args.get("server"),
        )

        for symbol, count in symbols.items():
            result[symbol] = {}
            service.set_symbol(symbol)
            for timeframe, start_pos in timeframes.items():
                candle_info = service.info(
                    timeframe=timeframe,
                    start_pos=start_pos,
                    count=count,
                )
                result[symbol][timeframe] = candle_info

        return jsonify(result), 200
    except Exception as error:
        logger.warning(f"Error in /info endpoint: {error}")
        return jsonify(result), 200


@api_bp.route("/account-info", methods=["POST"])
@auth()
def account_info():
    try:
        args = request.json or {}
        service = MT5Client(
            username=int(args.get("username")),
            password=args.get("password"),
            server=args.get("server"),
        )

        info = service.get_account_info()
        if info is None:
            return jsonify({"error": "could not fetch account info, check credentials/connection"}), 502

        return jsonify(info._asdict()), 200
    except Exception as error:
        logger.error(f"Error in /account-info: {error}")
        return jsonify({"error": str(error)}), 500


@api_bp.route("/positions", methods=["POST"])
@auth()
def positions():
    try:
        args = request.json or {}
        service = MT5Client(
            username=int(args.get("username")),
            password=args.get("password"),
            server=args.get("server"),
        )

        result = service.get_positions(args.get("symbol"))
        return jsonify(result), 200
    except Exception as error:
        logger.error(f"Error in /positions: {error}")
        return jsonify({"error": str(error)}), 500


@api_bp.route("/history", methods=["POST"])
@auth()
def history():
    try:
        args = request.json or {}
        service = MT5Client(
            username=int(args.get("username")),
            password=args.get("password"),
            server=args.get("server"),
        )

        now = datetime.now(timezone.utc)
        date_from = (
            datetime.fromisoformat(args["from"])
            if args.get("from")
            else now - timedelta(days=30)
        )
        date_to = (
            datetime.fromisoformat(args["to"])
            if args.get("to")
            else now
        )

        result = service.get_history(date_from, date_to)
        return jsonify(result), 200
    except Exception as error:
        logger.error(f"Error in /history: {error}")
        return jsonify({"error": str(error)}), 500


@api_bp.route("/trade", methods=["POST"])
@auth()
@validate()
def trade(body: Position):
    try:
        service = MT5Client(
            symbol=body.symbol,
            username=int(body.username),
            password=body.password,
            server=body.server,
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
        logger.error(f"Error in /trade: {error}")
        return jsonify({"error": str(error)}), 500


@api_bp.route("/close-position", methods=["POST"])
@auth()
@validate()
def close_position(body: ClosePosition):
    try:
        service = MT5Client(
            username=int(body.username),
            password=body.password,
            server=body.server,
        )

        result = service.close_position(body.ticket, comment=body.comment)
        return jsonify(result), 200
    except Exception as error:
        logger.error(f"Error in /close-position: {error}")
        return jsonify({"error": str(error)}), 500


@api_bp.route("/modify-position", methods=["POST"])
@auth()
@validate()
def modify_position(body: ModifyPosition):
    try:
        service = MT5Client(
            username=int(body.username),
            password=body.password,
            server=body.server,
        )

        result = service.modify_position(body.ticket, sl=body.sl, tp=body.tp)
        return jsonify(result), 200
    except Exception as error:
        logger.error(f"Error in /modify-position: {error}")
        return jsonify({"error": str(error)}), 500

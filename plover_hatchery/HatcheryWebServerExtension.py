from flask import Flask, jsonify, request
from threading import Thread
from flask.typing import ResponseClass
from urllib.parse import urlsplit
from werkzeug.serving import make_server
from plover.engine import StenoEngine

from .Store import store


LOCAL_WEB_HOSTS = {"localhost", "127.0.0.1", "::1"}
HATCHERY_WEB_HOSTS = {"hatchery.vaie.art"}


def is_allowed_origin(origin: str):
    try:
        parsed_origin = urlsplit(origin)
        parsed_origin.port
    except ValueError:
        return False

    if parsed_origin.path != "" or parsed_origin.query != "" or parsed_origin.fragment != "":
        return False

    hostname = parsed_origin.hostname
    if hostname is None:
        return False

    hostname = hostname.lower()

    if hostname in LOCAL_WEB_HOSTS:
        return parsed_origin.scheme in {"http", "https"}

    if hostname in HATCHERY_WEB_HOSTS:
        return parsed_origin.scheme == "https"

    return False

class HatcheryWebServerExtension:
    def __init__(self, engine: StenoEngine):
        app = Flask(__name__)

        self.__app = app
        self.__server = None
        self.__server_thread = None

        # Disable CORS
        @app.after_request
        def _(response: ResponseClass):
            origin = request.origin
            
            if origin is not None and is_allowed_origin(origin):
                response.headers.add("Access-Control-Allow-Origin", "*")

            response.headers.add("Access-Control-Allow-Methods", "GET,PATCH,PUT,POST,DELETE,OPTIONS")
            response.headers.add("Access-Control-Allow-Headers", "Content-Type")
            return response

        @app.route("/api/compile", methods=["POST"])
        def compile_route():
            try:
                request_body = request.get_json(silent=True) or {}
                refresh_cache = bool(request_body.get("refreshCache", False))
                return jsonify({
                    "dictionaries": store.compile_hatchery_dictionaries(refresh_cache=refresh_cache),
                })
            except Exception as e:
                return jsonify({
                    "error": str(e),
                }), 500
        
        @app.route("/api/breakdown_translation/<translation>")
        def breakdown_translation_route(translation: str):
            compile_result = self.__compile_hatchery_dictionaries()
            if compile_result is not None:
                return compile_result

            if store.breakdown_translation is None:
                return jsonify({
                    "error": "No compiled Hatchery lookup is available",
                }), 503

            breakdown = store.breakdown_translation(translation)
            if breakdown is None:
                return jsonify({})

            return breakdown
        
        @app.route("/api/breakdown_lookup/<outline>")
        def breakdown_lookup_route(outline: str):
            compile_result = self.__compile_hatchery_dictionaries()
            if compile_result is not None:
                return compile_result

            if store.breakdown_lookup is None or store.translations is None:
                return jsonify({
                    "error": "No compiled Hatchery lookup is available",
                }), 503

            breakdown = store.breakdown_lookup(tuple(outline.split(" ")), store.translations)
            if breakdown is None:
                return jsonify([])

            return breakdown

    def __compile_hatchery_dictionaries(self):
        try:
            store.compile_hatchery_dictionaries()
            return None
        except Exception as e:
            return jsonify({
                "error": str(e),
            }), 500
        
    def start(self):
        """Start the web server in a background thread"""
        try:
            
            self.__server = make_server("localhost", 5325, self.__app)
            
            self.__server_thread = Thread(target=self.__server.serve_forever)
            self.__server_thread.daemon = True
            self.__server_thread.start()
            
        except Exception as e:
            print(f"Failed to start Hatchery web server: {e}")

    def stop(self):
        """Stop the web server"""
        if self.__server:
            self.__server.shutdown()
            self.__server_thread.join(timeout=5)

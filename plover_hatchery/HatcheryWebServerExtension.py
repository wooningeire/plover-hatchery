import re
from flask import Flask, jsonify, request
from threading import Thread
from flask.typing import ResponseClass
from werkzeug.serving import make_server
from plover.engine import StenoEngine

from .Store import store


allowed_origins = re.compile(r"https?://localhost:\d+|https://vaie\.art")

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
            
            if allowed_origins.match(origin):
                response.headers.add("Access-Control-Allow-Origin", "*")

            response.headers.add("Access-Control-Allow-Methods", "GET,PATCH,PUT,POST,DELETE,OPTIONS")
            return response
        
        @app.route("/api/breakdown_translation/<translation>")
        def breakdown_translation_route(translation: str):
            breakdown = store.breakdown_translation(translation)
            if breakdown is None:
                return jsonify({})

            return breakdown
        
        @app.route("/api/breakdown_lookup/<outline>")
        def breakdown_lookup_route(outline: str):
            breakdown = store.breakdown_lookup(tuple(outline.split(" ")), store.translations)
            if breakdown is None:
                return jsonify([])

            return breakdown
        
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
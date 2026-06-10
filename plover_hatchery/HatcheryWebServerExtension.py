from flask import Flask, Response, jsonify, request
from threading import Thread
from flask.typing import ResponseClass
from urllib.parse import urlsplit
from werkzeug.serving import make_server
from plover.engine import StenoEngine

from .Store import store
from .lib.dictionary.write_entries import (
    AddEntryValidationError,
    UnknownHatcheryDictionaryError,
    add_entry_to_hatchery_dictionary,
    delete_entry_from_hatchery_dictionary,
    hatchery_dictionary_summaries,
    list_hatchery_dictionary_entries,
)


LOCAL_WEB_HOSTS = {"localhost", "127.0.0.1", "::1"}
HATCHERY_WEB_HOSTS = {"vaie.art"}
HATCHERY_SERVICE_ID = "plover-hatchery"


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

        @app.route("/api/status")
        def status_route():
            return jsonify({
                "service": HATCHERY_SERVICE_ID,
                "ok": True,
            })

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

        @app.route("/api/dictionaries")
        def dictionaries_route():
            return jsonify({
                "dictionaries": hatchery_dictionary_summaries(),
            })

        @app.route("/api/entries", methods=["GET"])
        def entries_route():
            try:
                return jsonify(list_hatchery_dictionary_entries(
                    dictionary_path=request.args.get("dictionaryPath"),
                    offset=request.args.get("offset"),
                    limit=request.args.get("limit"),
                    query=request.args.get("query"),
                    resolve_translations=request.args.get("resolveTranslations"),
                ))
            except UnknownHatcheryDictionaryError as e:
                return jsonify({
                    "error": str(e),
                }), 404
            except AddEntryValidationError as e:
                return jsonify({
                    "error": str(e),
                }), 400
            except Exception as e:
                return jsonify({
                    "error": str(e),
                }), 500

        @app.route("/api/entries", methods=["POST"])
        def add_entry_route():
            try:
                request_body = request.get_json(silent=True) or {}
                if not isinstance(request_body, dict):
                    raise AddEntryValidationError("Expected a JSON object")

                return jsonify(add_entry_to_hatchery_dictionary(
                    dictionary_path=request_body.get("dictionaryPath"),
                    translation=request_body.get("translation"),
                    definition=request_body.get("definition"),
                    entry_format=request_body.get("format"),
                ))
            except UnknownHatcheryDictionaryError as e:
                return jsonify({
                    "error": str(e),
                }), 404
            except AddEntryValidationError as e:
                return jsonify({
                    "error": str(e),
                }), 400
            except Exception as e:
                return jsonify({
                    "error": str(e),
                }), 500

        @app.route("/api/entries", methods=["DELETE"])
        def delete_entry_route():
            try:
                request_body = request.get_json(silent=True) or {}
                if not isinstance(request_body, dict):
                    raise AddEntryValidationError("Expected a JSON object")

                return jsonify(delete_entry_from_hatchery_dictionary(
                    dictionary_path=request_body.get("dictionaryPath"),
                    entry_key=request_body.get("entryKey"),
                ))
            except UnknownHatcheryDictionaryError as e:
                return jsonify({
                    "error": str(e),
                }), 404
            except AddEntryValidationError as e:
                return jsonify({
                    "error": str(e),
                }), 400
            except Exception as e:
                return jsonify({
                    "error": str(e),
                }), 500
        
        @app.route("/api/breakdown_translation/<translation>")
        def breakdown_translation_route(translation: str):
            try:
                compile_result = self.__compile_hatchery_dictionaries()
                if compile_result is not None:
                    return compile_result

                breakdown = store.breakdown_hatchery_translation(translation)

                if breakdown is None and store.breakdown_translation is None:
                    return jsonify({
                        "error": "No compiled Hatchery lookup is available",
                    }), 503

                if breakdown is None:
                    breakdown = store.breakdown_translation(translation)

                if breakdown is None:
                    return jsonify({})

                return Response(breakdown, mimetype="application/json")
            except Exception as e:
                return jsonify({
                    "error": str(e),
                }), 500
        
        @app.route("/api/breakdown_lookup/<outline>")
        def breakdown_lookup_route(outline: str):
            try:
                compile_result = self.__compile_hatchery_dictionaries()
                if compile_result is not None:
                    return compile_result

                breakdown = store.breakdown_hatchery_lookup(tuple(outline.split(" ")))

                if breakdown is None and (store.breakdown_lookup is None or store.translations is None):
                    return jsonify({
                        "error": "No compiled Hatchery lookup is available",
                    }), 503

                if breakdown is None:
                    breakdown = store.breakdown_lookup(tuple(outline.split(" ")), store.translations)

                if breakdown is None:
                    return jsonify([])

                return Response(breakdown, mimetype="application/json")
            except Exception as e:
                return jsonify({
                    "error": str(e),
                }), 500

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

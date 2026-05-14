from flask import jsonify
from werkzeug.exceptions import HTTPException


def register_error_handlers(app):
    @app.errorhandler(HTTPException)
    def handle_http_exception(error):
        return (
            jsonify({"error": error.description, "code": error.name.lower().replace(" ", "_")}),
            error.code,
        )

    @app.errorhandler(413)
    def too_large(error):
        return jsonify({"error": "Uploaded file is too large.", "code": "file_too_large"}), 413

    @app.errorhandler(Exception)
    def handle_generic(error):
        if isinstance(error, HTTPException):
            return handle_http_exception(error)
        app.logger.exception("Unhandled exception: %s", error)
        message = str(error) if app.config.get("DEBUG") else "Internal server error"
        return jsonify({"error": message, "code": "server_error"}), 500

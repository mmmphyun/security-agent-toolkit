from flask import Flask
from routes.auth import auth_bp
from routes.events import events_bp
from routes.notes import notes_bp
from auth_helpers import configure_session, no_cache
from error_handlers import register_error_handlers

app = Flask(__name__)
app.json.ensure_ascii = False
configure_session(app, "monitor_session")
app.register_blueprint(auth_bp)
app.register_blueprint(events_bp)
app.register_blueprint(notes_bp)
register_error_handlers(app)
app.after_request(no_cache)

if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5200)

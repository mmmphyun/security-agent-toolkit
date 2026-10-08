from flask import Flask
from routes.posts import posts_bp
from routes.auth import auth_bp
from auth_helpers import configure_session, no_cache, template_auth
from error_handlers import register_error_handlers
from request_logging import record_request

app = Flask(__name__)
app.json.ensure_ascii = False
configure_session(app, "general_session")
app.register_blueprint(posts_bp)
app.register_blueprint(auth_bp)
app.context_processor(template_auth)
register_error_handlers(app)
app.after_request(no_cache)
app.after_request(record_request)

if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5100)

import os
from flask import Flask, jsonify
from werkzeug.middleware.proxy_fix import ProxyFix

from config import get_config
from extensions import db, migrate, jwt, bcrypt, mail, cors


def create_app(config_class=None):
    app = Flask(__name__, template_folder="../templates")
    app.config.from_object(config_class or get_config())

    app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1, x_prefix=1)

    os.makedirs(app.config["DATA_DIR"], exist_ok=True)
    os.makedirs(app.config["STORES_DIR"], exist_ok=True)

    db.init_app(app)
    migrate.init_app(app, db)
    jwt.init_app(app)
    bcrypt.init_app(app)
    mail.init_app(app)
    cors.init_app(
        app,
        resources={r"/api/*": {"origins": app.config["ALLOWED_ORIGINS"]}},
        supports_credentials=True,
    )

    from app.models import user, store, dataset, audit_log, password_reset, scheduled_job  # noqa: F401

    from app.blueprints.health.routes import bp as health_bp
    from app.blueprints.auth.routes import bp as auth_bp
    from app.blueprints.admin.routes import bp as admin_bp
    from app.blueprints.store.routes import bp as store_bp
    from app.blueprints.analytics.routes import bp as analytics_bp

    app.register_blueprint(health_bp, url_prefix="/api")
    app.register_blueprint(auth_bp, url_prefix="/api/auth")
    app.register_blueprint(admin_bp, url_prefix="/api/admin")
    app.register_blueprint(store_bp, url_prefix="/api/store")
    app.register_blueprint(analytics_bp, url_prefix="/api/analytics")

    from app.errors import register_error_handlers
    register_error_handlers(app)

    from app.cli import register_cli
    register_cli(app)

    from app.services.scheduler_service import init_scheduler
    init_scheduler(app)

    @app.route("/")
    def index():
        return jsonify(
            {
                "name": "Assortment Dashboard API",
                "version": "3.0.0",
                "status": "running",
                "docs": "/api/health",
            }
        )

    with app.app_context():
        try:
            from app.services.auth_service import ensure_super_admin
            ensure_super_admin()
        except Exception as exc:
            app.logger.warning("Could not bootstrap super admin yet: %s", exc)

    return app

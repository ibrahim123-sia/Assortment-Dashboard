import os
import click
from flask.cli import with_appcontext

from extensions import db
from app.services import auth_service


def register_cli(app):
    @app.cli.command("seed-admin")
    @with_appcontext
    def seed_admin():
        """Bootstrap the super admin from env."""
        admin = auth_service.ensure_super_admin()
        click.echo(f"Super admin ready: {admin.email}")

    @app.cli.command("seed-demo")
    @with_appcontext
    def seed_demo():
        """Create a Demo Store with manager and load existing CSV as active dataset."""
        from app.models import User, Store, UserRole
        from app.services import dataset_service

        admin = auth_service.ensure_super_admin()
        store = Store.query.filter_by(slug="demo-store").first()
        if not store:
            store = Store(
                name="Demo Store",
                slug="demo-store",
                description="Sample multi-tenant store seeded from legacy CSV.",
                contact_email="demo@example.com",
                theme_mode="light",
                brand_primary_color="#2563eb",
                is_active=True,
                created_by_user_id=admin.id,
            )
            db.session.add(store)
            db.session.flush()

        manager = User.query.filter_by(email="demo@example.com").first()
        if not manager:
            manager = User(
                email="demo@example.com",
                password_hash=auth_service.hash_password("Demo@12345"),
                role=UserRole.STORE_MANAGER,
                full_name="Demo Manager",
                is_email_verified=True,
                is_active=True,
                must_change_password=False,
                store_id=store.id,
            )
            db.session.add(manager)
            db.session.commit()

        click.echo(f"Demo store ready (slug=demo-store, manager=demo@example.com / Demo@12345)")

        legacy_csv = None
        candidates = [
            os.path.join(app.config["BASE_DIR"], "..", "data", "Online_Retail_II_Cleaned.csv"),
            os.path.join(app.config["DATA_DIR"], "Online_Retail_II_Cleaned.csv"),
            os.path.join(app.config["BASE_DIR"], "data", "Online_Retail_II_Cleaned.csv"),
        ]
        for p in candidates:
            if os.path.exists(p):
                legacy_csv = p
                break

        if legacy_csv and not store.active_dataset_id:
            from werkzeug.datastructures import FileStorage
            with open(legacy_csv, "rb") as fh:
                fs = FileStorage(stream=fh, filename="Online_Retail_II_Cleaned.csv", content_type="text/csv")
                result = dataset_service.process_upload(store, fs, manager)
            if result.get("ok"):
                click.echo(f"Seeded dataset: {result['dataset'].original_filename} ({result['dataset'].row_count} rows)")
            else:
                click.echo(f"Could not seed dataset: {result.get('error')}")
        elif not legacy_csv:
            click.echo("Legacy CSV not found; skipping dataset seed.")
        else:
            click.echo("Demo store already has an active dataset; skipping CSV seed.")

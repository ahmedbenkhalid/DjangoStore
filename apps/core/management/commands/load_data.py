"""
Load seed data from fixtures/ directory.

Usage:
    python manage.py load_data                # load all fixtures
    python manage.py load_data --clear        # clear data first, then load
    python manage.py load_data --file auth_user.json  # load specific file
"""

import json
from pathlib import Path

from django.apps import apps
from django.core.management.base import BaseCommand
from django.db import connection

FIXTURES_DIR = Path(__file__).resolve().parent.parent.parent.parent.parent / "fixtures"

# Load order matters — dependencies first
LOAD_ORDER = [
    "auth_user.json",
    "users_profile.json",
    "users_address.json",
    "products_category.json",
    "products_brand.json",
    "products_tag.json",
    "products_product.json",
    "products_product_tags.json",  # M2M through — after products and tags
    "products_review.json",
    "products_wishlist.json",
    "orders_order.json",
    "orders_orderitem.json",
    "cart_cart.json",
    "cart_cartitem.json",
]


class Command(BaseCommand):
    help = "Load seed data from JSON fixture files"

    def add_arguments(self, parser):
        parser.add_argument(
            "--clear",
            action="store_true",
            help="Clear all data from tables before loading",
        )
        parser.add_argument(
            "--file",
            type=str,
            help="Load a specific fixture file (e.g. products_category.json)",
        )

    def handle(self, *args, **options):
        if not FIXTURES_DIR.exists():
            self.stderr.write(
                self.style.ERROR(f"Fixtures directory not found: {FIXTURES_DIR}")
            )
            return

        clear = options["clear"]
        single_file = options["file"]

        if clear:
            self._clear_data()

        files_to_load = (
            [FIXTURES_DIR / single_file]
            if single_file
            else [
                FIXTURES_DIR / name
                for name in LOAD_ORDER
                if (FIXTURES_DIR / name).exists()
            ]
        )

        total_loaded = 0
        for fixture_path in files_to_load:
            if not fixture_path.exists():
                self.stderr.write(
                    self.style.WARNING(
                        f"  [!]  {fixture_path.name} not found, skipping"
                    )
                )
                continue

            count = self._load_fixture(fixture_path)
            total_loaded += count

        self.stdout.write(
            self.style.SUCCESS(f"\n  [OK]  Loaded {total_loaded} records total")
        )

    def _load_fixture(self, path: Path) -> int:
        data = json.loads(path.read_text(encoding="utf-8"))
        if not data:
            return 0

        model_label = data[0]["model"]
        is_m2m_through = "_tags" in path.stem

        if is_m2m_through:
            return self._load_m2m_through(path.name, model_label, data)
        else:
            return self._load_objects(path.name, model_label, data)

    def _load_objects(self, filename: str, model_label: str, data: list[dict]) -> int:
        try:
            model = apps.get_model(model_label)
        except LookupError:
            self.stderr.write(
                self.style.ERROR(f"  [X]  Model '{model_label}' not found")
            )
            return 0

        count = 0
        skipped = 0

        for record in data:
            pk = record["pk"]
            fields = record["fields"]

            # Strip auto_now/auto_now_add fields — Django manages them
            for fname in list(fields.keys()):
                try:
                    field = model._meta.get_field(fname)
                    if getattr(field, "auto_now", False) or getattr(
                        field, "auto_now_add", False
                    ):
                        del fields[fname]
                except Exception:
                    pass  # field might not exist as a model field (e.g. from through table)

            try:
                _, created = model.objects.update_or_create(pk=pk, defaults=fields)
                if created:
                    count += 1
                else:
                    skipped += 1
            except Exception as e:
                self.stderr.write(
                    self.style.WARNING(f"  [!]  {model_label} pk={pk}: {e}")
                )

        status = f"  [OK]  {filename}: {count} created"
        if skipped:
            status += f", {skipped} updated"
        self.stdout.write(self.style.SUCCESS(status))
        return count + skipped

    def _load_m2m_through(
        self, filename: str, model_label: str, data: list[dict]
    ) -> int:
        """Load M2M through table entries using raw SQL."""
        # Derive table name from model label
        # "products.Product_tags" → "products_product_tags"
        app, model_name = model_label.split(".")
        table_name = f"{app}_{model_name}".lower()

        if not data:
            return 0

        # Through table fixture fields already have _id suffix: {"product_id": 1, "tag_id": 1}
        first_fields = data[0]["fields"]
        fk_columns = list(first_fields.keys())

        count = 0
        with connection.cursor() as cursor:
            for record in data:
                pk = record["pk"]
                values = [record["fields"][c] for c in fk_columns]
                cols_sql = ", ".join(fk_columns)
                placeholders = ", ".join("?" for _ in fk_columns)
                sql = f"INSERT OR IGNORE INTO {table_name} (id, {cols_sql}) VALUES (?, {placeholders})"
                try:
                    cursor.execute(sql, [pk] + values)
                    if cursor.rowcount:
                        count += 1
                except Exception as e:
                    self.stderr.write(
                        self.style.WARNING(f"  [!]  {table_name} id={pk}: {e}")
                    )

        self.stdout.write(
            self.style.SUCCESS(f"  [OK]  {filename}: {count} M2M relations loaded")
        )
        return count

    def _clear_data(self):
        """Clear all data from project tables (preserves schema)."""
        self.stdout.write(self.style.WARNING("  [i]  Clearing existing data..."))

        # Delete in reverse dependency order
        clear_order = [
            "cart_cartitem",
            "cart_cart",
            "orders_orderitem",
            "orders_order",
            "products_wishlist",
            "products_review",
            "products_product_tags",
            "products_product",
            "products_tag",
            "products_brand",
            "products_category",
            "users_address",
            "users_profile",
            "auth_user",
        ]

        with connection.cursor() as cursor:
            cursor.execute("PRAGMA foreign_keys = OFF")
            for table in clear_order:
                try:
                    cursor.execute(f"DELETE FROM {table}")
                    self.stdout.write(f"    Cleared {table}")
                except Exception:
                    pass
            cursor.execute("PRAGMA foreign_keys = ON")

        self.stdout.write(self.style.SUCCESS("  [OK]  Data cleared\n"))

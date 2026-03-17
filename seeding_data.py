#!/usr/bin/env python
"""
Script to load fake data fixtures into the database.
"""

import os
import django


os.environ.setdefault("DJANGO_SETTINGS_MODULE", "shop.settings")
django.setup()

from django.core.management import call_command  # noqa: E402


def load_fixtures():
    fixtures = [
        "fixtures/categories.json",
        "fixtures/brands.json",
        "fixtures/tags.json",
        "fixtures/products.json",
        "fixtures/users.json",
        "fixtures/profiles.json",
        "fixtures/orders.json",
        "fixtures/order_items.json",
        "fixtures/reviews.json",
        "fixtures/wishlists.json",
    ]

    print("Loading fake data fixtures...\n")

    for fixture in fixtures:
        print(f"Loading {fixture}...")
        call_command("loaddata", fixture, verbosity=1)

    print("\n" + "=" * 50)
    print("Fake data loaded successfully!")
    print("=" * 50)
    print("\nAdmin login:")
    print("  Username: vhmd")
    print("  Password: 123")
    print("\nRegular user login:")
    print("  Username: john_doe")
    print("  Password: password123")


if __name__ == "__main__":
    load_fixtures()

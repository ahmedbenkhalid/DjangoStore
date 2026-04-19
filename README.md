# Django E-Commerce Platform

Full-stack e-commerce platform for laptops & smartphones with Arabic/English (RTL) support.

## Features

- Product catalog with categories, brands, and filtering
- Shopping cart with session management
- Order processing and management
- User authentication and profile management
- Wishlist and product reviews
- Arabic/English internationalization (i18n)

## Tech Stack

| Layer | Technology |
|---|---|
| Backend | Django 6.0.3, Python 3.14+ |
| Database | SQLite3 |
| Frontend | Tailwind CSS 3, Alpine.js, HTMX |
| UI Components | Flowbite |
| Admin | django-jazzmin (dark theme) |
| i18n | EN/AR with Readex Pro font |
| Async | Celery + Redis |

## Quick Start

### Prerequisites

- Python 3.14+
- Node.js 18+ (for Tailwind CSS)
- Redis (for Celery)

### Installation

```bash
./joi setup
./joi server
```

Visit: <http://localhost:8000>

## Project Structure

```
apps/
├── core/          # Home, banners, shared views
├── users/        # Auth, dashboard, addresses
├── products/     # Products, categories, wishlist, reviews
├── cart/         # Session-based shopping cart
└── orders/       # Checkout, order management

templates/
├── shared/       # base.html + global partials
└── emails/       # Email templates
```

## Commands

| Command | Description |
|---|---|
| `./joi server` | Start dev server (port 8000) |
| `./joi migrate` | Run database migrations |
| `./joi seed` | Seed database with fixtures |
| `./joi admin` | Create admin user |
| `./joi lint` | Run linting checks |
| `npm run build:css` | Build Tailwind CSS |
| `npm run watch:css` | Watch mode for CSS |
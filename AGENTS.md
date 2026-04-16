# SMART S3R — Django E-Commerce Platform

Full-stack e-commerce platform for laptops & smartphones. Arabic/English (RTL) support.

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Backend | Django 6.0.3, Python 3.14+ |
| Database | SQLite3 (dev) |
| Frontend | Tailwind CSS 3 + Alpine.js, HTMX |
| UI Components | **Flowbite ONLY** - no custom CSS |
| Admin | django-jazzmin (dark theme) |
| i18n | EN/AR with `Readex Pro` font |
| Async | Celery + Redis |
| Dev Tools | debug-toolbar, browser-reload, ruff |

## Project Structure

```
apps/
├── core/          ← Home, banners, shared views
├── users/         ← Auth, dashboard, addresses
├── products/      ← Products, categories, wishlist, reviews
├── cart/          ← Session-based shopping cart
└── orders/        ← Checkout, order management

templates/
├── shared/        ← base.html + global partials
└── emails/        ← Email templates

users/templates/users/
├── dashboard.html         ← Single-view dashboard with tab navigation
└── dashboard/            ← Dashboard fragment templates
    ├── _personal.html
    ├── _orders.html
    ├── _addresses.html
    ├── _security.html
    └── _wishlist.html

static/
├── css/           ← Tailwind output (tailwind.css)
└── js/            ← Alpine.js stores (alpine-store.js)
```

---

## Commands

### Development
```bash
./joi server              # Start dev server (port 8000)
./joi migrate            # Run database migrations
./joi seed               # Seed database with fixtures
./joi admin              # Create admin user
```

### CSS Build
```bash
npm run build:css        # Build Tailwind CSS (production)
npm run watch:css        # Watch mode for development
```

### Linting
```bash
ruff check .             # Lint all files
ruff check --fix .       # Lint and auto-fix
ruff check path/to/file.py  # Lint single file
```

### Testing
```bash
python manage.py test                    # Run all tests
python manage.py test app.tests           # Run specific app tests
python manage.py test app.tests.TestClass # Run specific test class
python manage.py test app.tests.TestClass.test_method  # Run single test
python manage.py test --verbosity=2       # Verbose output
```

---

## Code Style Guidelines

### Python/Django

**Imports (Alphabetical)**
```python
# Standard library first
from django.conf import settings
from django.contrib.auth import get_user_model
from django.db import models

# Third party
from celery import shared_task

# Local apps
from apps.products.models import Product
```

**Naming Conventions**
- Classes: `PascalCase` (e.g., `ProductSerializer`)
- Functions/variables: `snake_case` (e.g., `get_cart_total`)
- Constants: `UPPER_SNAKE_CASE` (e.g., `DEFAULT_PAGE_SIZE`)
- Models: singular, descriptive (e.g., `OrderItem` not `OrderItems`)

**Django Best Practices**
- Use `gettext_lazy` (`_`) for all user-facing strings
- Use `select_related()` and `prefetch_related()` for query optimization
- Use `get_object_or_404()` for single object retrieval
- Use CBVs (Class-Based Views) for complex views
- Keep business logic in models/services, not views

**Error Handling**
- Use Django's messaging framework for user feedback
- Return appropriate HTTP status codes
- Log errors with proper levels (`logger.error`, `logger.exception`)
- Never expose sensitive data in error responses

---

### JavaScript (Alpine.js + HTMX)

**Alpine.js Patterns**
```html
<!-- Basic component -->
<div x-data="{ count: 0 }">
    <button x-on:click="count++">Increment</button>
    <span x-text="count"></span>
</div>

<!-- With methods -->
<div x-data="{ 
    submitting: false,
    async submit() {
        this.submitting = true;
        // HTMX form submission
        this.submitting = false;
    }
}">
```

**HTMX Patterns**
```html
<!-- HTMX form with Alpine state -->
<form hx-post="/endpoint/"
      hx-target="#result-container"
      hx-swap="innerHTML"
      @htmx:after-on-load="if(event.detail.successful) { /* success */ }">
```

**Alpine Store (Cart Example)**
```javascript
// static/js/alpine-store.js
document.addEventListener('alpine:init', () => {
    Alpine.store('cart', {
        items: [],
        addToCart(form) { /* implementation */ },
        showOffcanvas() { /* implementation */ }
    });
});
```

**Guidelines**
- Always use `{% csrf_token %}` with HTMX POST forms
- Use `@htmx:after-on-load` for post-request actions
- Use `hx-swap="innerHTML"` for partial updates
- Initialize Flowbite components after HTMX swaps:
  ```javascript
  @htmx:after-on-load="if (window.initFlowbite) window.initFlowbite()"
  ```

---

### Templates (Django + Tailwind + Flowbite)

**⚠️ UI MANDATE: Flowbite Components ONLY**
- **NO custom CSS** - Use only Flowbite component classes
- **Use Tailwind utilities** for layout/spacing only
- **Use custom color tokens** (see below), not default Tailwind colors

**Flowbite Components to Use:**
- Buttons: `bg-corporate-600 hover:bg-corporate-700 text-white`
- Cards: `bg-white border border-surface-200 rounded-lg p-6`
- Forms: `border border-surface-200 rounded-lg focus:ring-2 focus:ring-corporate-500`
- Badges: `bg-green-100 text-green-800 rounded-full px-2.5 py-0.5`
- Tabs: Flowbite tab component structure
- Modals: Flowbite modal with Alpine triggers

**Tailwind Custom Colors (REQUIRED):**
```
corporate-600: #1A56DB  (primary brand)
surface-50/100/200:    (backgrounds, borders)
charcoal-900/700/500/400: (text hierarchy)
```
⚠️ **NEVER use**: `text-gray-*`, `bg-gray-*`, `border-gray-*` - these won't render!

**RTL Support:**
- Use `start-`/`end-` instead of `left-`/`right-`
- Use `ms-`/`me-` instead of `ml-`/`mr-`
- Use `ps-`/`pe-` instead of `pl-`/`pr-`

**Template Structure:**
- Base template: `shared/base.html`
- Partial templates: `shared/partials/`
- App templates: `apps/{app}/templates/{app}/`

---

### HTML Template Example (Profile Dashboard)

```html
<!-- Flowbite Tabs -->
<ul class="flex flex-wrap -mb-px text-sm font-medium text-center" role="tablist">
    <li class="me-2">
        <button @click="switchTab('personal')"
                class="inline-flex items-center gap-2 p-4 border-b-2 rounded-t-lg"
                :class="activeTab === 'personal' ? 'text-corporate-600 border-corporate-600' : 'text-charcoal-500 border-transparent'">
            <i class="bi bi-person"></i>
            <span>{% trans "Personal" %}</span>
        </button>
    </li>
</ul>

<!-- Flowbite Card -->
<div class="bg-white border border-surface-200 rounded-lg p-6">
    <h3 class="font-semibold text-charcoal-900 mb-4">{% trans "Personal Info" %}</h3>
    <!-- Form fields -->
</div>

<!-- Flowbite Button -->
<button type="submit" class="px-5 py-2.5 bg-corporate-600 text-white font-medium rounded-lg hover:bg-corporate-700">
    {% trans "Save" %}
</button>
```

---

## URL Routes

| Path | View | Name |
|------|------|------|
| `/` | home | `home` |
| `/products/` | product_list | `products:products` |
| `/products/<slug>/` | product_detail | `products:detail` |
| `/cart/` | cart_detail | `cart:detail` |
| `/orders/checkout/` | checkout | `orders:checkout` |
| `/profile/` | profile | `profile` |

---

## Models Summary

### products
- **Product**: name, price, discount_price, stock, category(FK), brand(FK)
- **Category**: name, slug, image
- **Wishlist**: user(FK), product(FK)

### users
- **Profile**: user(O2O), phone, avatar, date_of_birth, gender
- **Address**: user(FK), name, phone, address, city, area, is_default

### orders
- **Order**: user(FK), status, total_amount, shipping_address, phone
- **OrderItem**: order(FK), product(FK), quantity, price

---

## Context Processors

Available in all templates: `menu_categories`, `wishlist`, `cart`
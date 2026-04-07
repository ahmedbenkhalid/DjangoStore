# SMART S3R — Django E-Commerce Platform

Full-stack e-commerce platform for laptops & smartphones. Arabic/English (RTL) support.

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Backend | Django 6.0.3, Python 3.14+ |
| Database | SQLite3 (dev) |
| Frontend | Tailwind CSS 3 + Flowbite, Alpine.js, HTMX |
| UI Components | django-cotton (`<c-*>` tags) |
| Admin | django-jazzmin (dark theme) |
| i18n | EN/AR with `Readex Pro` font |
| Async | Celery + Redis |
| Dev Tools | debug-toolbar, browser-reload, ruff |

## Project Structure

```
apps/
├── core/          ← Home, banners, shared views
├── users/         ← Auth, profile, addresses
├── products/      ← Products, categories, wishlist, reviews
├── cart/          ← Session-based shopping cart
└── orders/        ← Checkout, order management

templates/
├── cotton/        ← Django Cotton UI component library
├── shared/        ← base.html + global partials
└── emails/        ← Email templates

static/
├── css/           ← Tailwind output (tailwind.css)
└── js/            ← Alpine.js stores (alpine-store.js)
```

## URL Routes

| Path | View | Name |
|------|------|------|
| `/` | home view | `home` |
| `/search/` | product_list | `search` |
| `/products/` | product_list | `products:products` |
| `/products/<slug>/` | product_detail | `products:detail` |
| `/products/wishlist/` | wishlist_list | `wishlist` |
| `/categories/` | category_list | `categories:categories` |
| `/categories/<slug>/` | category_detail | `categories:detail` |
| `/cart/` | cart_detail | `cart:detail` |
| `/cart/add/<id>/` | cart_add | `cart:add` |
| `/cart/remove/<id>/` | cart_remove | `cart:remove` |
| `/cart/fragment/` | offcanvas_fragment | `cart:offcanvas_fragment` |
| `/orders/checkout/` | checkout | `orders:checkout` |
| `/orders/create_order/` | create_order | `orders:create_order` |
| `/orders/orders/` | order_list | `orders:order_list` |
| `/orders/orders/<id>/` | order_detail | `orders:order_detail` |
| `/login/` | login_view | `login` |
| `/register/` | register | `register` |
| `/logout/` | LogoutView | `logout` |
| `/profile/` | profile | `profile` |
| `/users/addresses/` | address_list | `users:address_list` |
| `/set-language/` | set_language_custom | `set_language_custom` |

## Models

### products
- **Category**: name, name_ar, slug, image, image_link
- **Brand**: name, name_ar, slug
- **Product**: name, name_ar, slug, sku, img, img_link, price, discount_price, stock, description, description_ar, external_link, category(FK), brand(FK), tags(M2M)
  - Properties: `current_price`, `on_sale`, `discount_percent`
- **Review**: product(FK), user(FK→Profile), rating(1-5), comment
- **Wishlist**: user(FK→Profile), product(FK)

### users
- **Profile**: user(O2O→User), first_name, last_name, avatar, phone, address, date_of_birth, gender, email_marketing, push_notifications
- **Address**: user(FK→User), name, phone, address, city, area, is_default

### cart
- **Cart**: user(O2O→User). Property: `total`
- **CartItem**: cart(FK), product(FK), quantity. Property: `subtotal`

### orders
- **Order**: user(FK), status, payment_method, payment_status, total_amount, shipping_address, phone, notes
  - Status: PENDING, CONFIRMED, PROCESSING, SHIPPED, DELIVERED, CANCELLED, REFUNDED
- **OrderItem**: order(FK), product(FK), quantity, price. Property: `subtotal`

### core
- **Banner**: image, title, title_ar, subtitle, subtitle_ar, link, link_text, link_text_ar, order, is_active

## Cotton Components (UI Library)

All components use `<c-vars>` for props and support `class` and `attrs` passthrough.

### Layout
- `<c-navbar />` — Sticky navbar with mega menu, search, cart, auth
- `<c-footer />` — Multi-column footer with newsletter
- `<c-brand />` — Logo link

### UI Elements
- `<c-badge variant="" size="" />` — Variants: default, secondary, destructive, success, warning, info, outline, dark
- `<c-button variant="" size="" tag="" />` — Variants: default, destructive, outline, secondary, ghost, link, dark. Sizes: xs, sm, default, lg, icon
- `<c-input />` — Flowbite-styled input
- `<c-textarea />` — Flowbite-styled textarea
- `<c-select />` — Flowbite-styled select
- `<c-checkbox />` — Flowbite-styled checkbox
- `<c-label />` — Form label
- `<c-separator />` — Horizontal/vertical divider
- `<c-progress value="" min="" max="" />` — Progress bar
- `<c-alert variant="" />` — Variants: default, success, error, warning, info, destructive

### Complex Components
- `<c-tabs default_value="">` — Alpine.js controlled tabs
- `<c-dialog default_open="">` — Alpine.js modal
- `<c-sheet default_open="" side="">` — Slide-over panel
- `<c-dropdown_menu>` — Alpine.js dropdown
- `<c-toast id="" title="" description="" type="">` — Toast notification
- `<c-table>` — Flowbite table
- `<c-card>` — Card wrapper

### Feature Components
- `<c-product_card :product="" />` — Product card with image, price, sale badge, stock badge, quick-add, zoom
- `<c-filter.drawer />` — Mobile filter drawer with HTMX live filtering

## Tailwind Color Tokens

```
corporate-600: #1A56DB  (primary)
surface-50/100/200:      (backgrounds, borders)
charcoal-900/700/500/400: (text hierarchy)
```

## Key Conventions

- **RTL**: Use `start-`/`end-`/`ms-`/`me-`/`ps-`/`pe-` (never `left-`/`right-`/`ml-`/`mr-`/`pl-`/`pr-`)
- **Arabic**: `text-lg` base, `leading-relaxed`, `font-readex`
- **No custom CSS**: Only Tailwind utility classes
- **Template paths**: App-level (e.g., `products/products.html`)
- **Base template**: `shared/base.html`
- **Context processors**: `menu_categories`, `wishlist`, `cart`

## Commands

```bash
./joi run             # Start dev server
npm run build:css     # Build CSS
npm run watch:css     # Watch CSS
ruff check .          # Lint
python manage.py migrate
```

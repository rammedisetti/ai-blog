# AI Blog Platform

Modern Django application that blends long-form editorial content with a lightweight digital product marketplace. Out of the box it supports account management, author/editor tooling, reader dashboards, and optional Razorpay-powered checkout for paid downloads.

---

## Project Layout

```
aiblogsite/         Django project configuration (settings, URLs, WSGI/ASGI)
accounts/           Custom `User` model, auth views, forms, templates
blog/               Editorial experience (posts, categories, dashboards, admin tools)
core/               Housekeeping management commands (`create_groups`)
ecommerce/          Digital product catalog, cart, checkout, Razorpay integration
media/, staticfiles/Uploaded assets and collected static files
requirements.txt    Python package lock
```

- Templates share `blog/base.html`, which loads Tailwind via CDN, HTMX, Alpine.js, and Font Awesome.
- Two settings modules ship with the project: `aiblogsite.settings` (production defaults) and `aiblogsite.settings-local` (development conveniences such as DEBUG on, local static files, SQLite).

---

## Key Capabilities

- **Authentication & Roles** – Custom `accounts.User` extends Django’s `AbstractUser` with profile, notification, and role metadata. Role changes automatically sync to `reader` and `author` groups (used by dashboard access checks).
- **Content Publishing** – `blog.Post` uses CKEditor-backed rich text, Many-to-Many relations for categories/tags, and counters for likes, saves, comments, and views. HTMX enhances admin moderation tables.
- **Reader & Author Dashboards** – Alpine.js driven tabbed layouts expose profile editing, saved/liked content, notification settings, password updates, and the new **Purchases** tab summarising order history with transaction IDs and generated invoice codes.
- **Admin Console** – Superusers land on `author_management`, a multi-tab workspace covering author onboarding, post moderation, comment queues, analytics placeholders, inventory management, and now order tracking plus sales metrics.
- **Digital Products & Checkout** – `ecommerce` app manages digital SKUs (`Product`), carts, orders, order items, and gateway receipts. Checkout can run in `normal` mode (placeholder) or Razorpay mode with hosted collection, signature verification, cart-to-order conversion, and a success receipt page.

---

## Data Model Highlights

- `accounts.User`
    - Primary key is UUID, preserving compatibility with existing Django auth APIs.
    - Fields for location, profession, DoB, interests (`JSONField`), and notification toggles.
    - `save()` hook ensures `reader`/`author` groups mirror the selected `role`.

- `blog`
    - `Post` (rich text, SEO metadata, status workflow, likes/saves Many-to-Many, revision tracking via `PostRevision`).
    - `Category`, `Tag` (taxonomy), `Comment` (moderation status), `UserSavedPost`, `Media`, `SiteSetting`.

- `ecommerce`
    - `Product` (digital goods, slug generation, discount support, tags, thumbnails, download counters).
    - `Cart` & `CartItem` (per-user, quantity-capped at 1 for digital SKU semantics).
    - `Order` & `OrderItem` (captures snapshot of cart at checkout).
    - `Payment` (one-to-one with order, stores gateway transaction metadata and status).

---

## Core Workflows

### Authentication & Authorization
1. Visitors hit `/accounts/auth_split/` which renders combined signup/login forms.
2. Successful signup/login flows call Django auth APIs and redirect to `home`.
3. The helper `dashboard_redirect` routes authenticated users to:
     - Reader dashboard (`reader_dashboard`) if role is `reader`.
     - Author dashboard (`author_dashboard`) if role is `author`.
     - Admin suite (`author_management`) if the user is a superuser.
4. Role-specific tabs display or hide edit controls and are protected with `@user_passes_test` group checks.

### Editorial Operations
- Authors create/update posts through `blog/add_post.html`, leveraging `ckeditor` for the `content` field.
- Admins moderate submissions and comments via HTMX-enabled tables in `author_management`.
- Readers can like, save, and comment on articles; saved posts show up in the dashboard.

### Ecommerce Lifecycle
1. **Catalog** – `ecommerce/product_list` shows digital products; detail pages live at `/ecommerce/products/<slug>/`.
2. **Cart** – `add_to_cart` / `buy_now` normalise quantity to 1 per item, reflecting single-license digital goods.
3. **Checkout** – `ecommerce:checkout` chooses between:
     - `checkout.html` (normal flow placeholder) when `ECOMMERCE_CHECKOUT_FLOW=normal`.
     - `razorpay_checkout.html` when `ECOMMERCE_CHECKOUT_FLOW=razorpay` and credentials exist.
4. **Razorpay Flow**
     - `_prepare_razorpay_checkout` creates or reuses an order via Razorpay SDK, storing the payload in the session.
     - Front-end uses Razorpay Checkout.js; upon success it POSTs to `checkout/razorpay/callback/`.
     - Server verifies signature, converts cart contents into `Order`/`OrderItem`, logs the `Payment`, clears the cart, and redirects to `checkout_success` with a receipt summary.
5. **Order Visibility** – All dashboards render the purchase history pulled by `_compose_order_history`, including transaction IDs, statuses, and generated invoice labels (`INV-<date>-<pk>`). Admin view adds aggregate metrics (captured vs pending orders, captured revenue).

---

## Environment & Setup

### Requirements
- Python 3.11+
- SQLite (default) or PostgreSQL (via `DATABASE_URL`)
- Node.js is **not** required (Tailwind/HTMX/Alpine served by CDN)

Install dependencies:
```bash
python -m venv .venv
.venv\Scripts\activate            # Windows
pip install --upgrade pip
pip install -r requirements.txt
```

### Environment Variables

| Variable | Purpose | Default |
| --- | --- | --- |
| `DJANGO_SETTINGS_MODULE` | Settings module. Use `aiblogsite.settings-local` for dev, `aiblogsite.settings` for prod. | `aiblogsite.settings` |
| `SECRET_KEY` | Required in production settings. | None |
| `DATABASE_URL` | Postgres connection URL (e.g. `postgres://…`). Falls back to SQLite when unset. | None |
| `ECOMMERCE_CHECKOUT_FLOW` | `normal` (default) or `razorpay`. | `normal` |
| `RAZORPAY_KEY_ID` / `RAZORPAY_KEY_SECRET` | Required when checkout flow is `razorpay`. | empty string |
| `RAZORPAY_CURRENCY` | Razorpay currency code (e.g. `INR`). | `INR` |

### Initialisation

```bash
python manage.py migrate
python manage.py create_groups       # ensures reader/author groups exist
python manage.py createsuperuser
```

Run the development server (local settings example):
```bash
set DJANGO_SETTINGS_MODULE=aiblogsite.settings-local
python manage.py runserver
```

Collect static files for deployment:
```bash
python manage.py collectstatic
```

### Razorpay Sandbox Setup
1. Set `ECOMMERCE_CHECKOUT_FLOW=razorpay` and provide sandbox `RAZORPAY_KEY_ID` / `RAZORPAY_KEY_SECRET`.
2. Restart the server to load credentials.
3. Add a paid product and complete checkout; successful captures appear in dashboards and the `Payment` table.

---

## Running Tests

The project ships with Django test scaffolding. Execute the test suite with:
```bash
python manage.py test
```

---

## Management Commands

| Command | Description |
| --- | --- |
| `python manage.py create_groups` | Ensures `reader` and `author` groups exist (idempotent; safe to run anytime). |

Add your own commands under `core/management/commands` following Django’s standard pattern.

---

## Front-end Notes

- Tailwind, HTMX, Alpine.js, and Font Awesome load from public CDNs via `blog/base.html`. No local build step is required.
- Tab interactions in dashboards rely on Alpine’s `x-data` / `x-show` directives. If you swap Alpine out, update the templates accordingly.
- Forms use `django-widget-tweaks` for inline styling, and CKEditor handles post authoring rich text.
- Razorpay Checkout.js is only loaded on the Razorpay template.

---

## Extending the Platform

- **New Content Types** – Add models and templates inside `blog/` and register them in `blog/urls.py`.
- **Additional Payment Providers** – Mirror the `_prepare_razorpay_checkout` pattern to plug in alternative gateways. Use `ECOMMERCE_CHECKOUT_FLOW` to branch between flows.
- **API Layer** – Install Django REST Framework and expose data as needed; existing views rely on server-rendered templates but models are REST-friendly.
- **Notifications** – Hook into `Payment` creation or `Order` status changes for emails/webhooks.

For large changes, ensure new commands or settings are documented under the relevant sections above.

---

## Troubleshooting

- **Group-based access denied** – Run `python manage.py create_groups` and ensure each user’s `role` is set correctly in the admin.
- **Razorpay checkout disabled** – Verify the checkout flow env var and credentials. The template falls back to the normal flow when totals are `0` or credentials are missing.
- **Static assets missing in production** – Run `collectstatic` and configure `STATIC_ROOT` (already set to `/staticfiles` in settings). Ensure your web server serves the collected directory.

Happy hacking! Reach out via `contact` page or GitHub issues for feature requests.

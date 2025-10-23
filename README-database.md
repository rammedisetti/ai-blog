# Database Overview

This document describes the relational database schema used by the **AI Blog** project. It covers the purpose of the database, tables and columns, indexes, keys, and other relevant information for maintainers.

## Purpose and Scope

The database stores all persistent data for the AI Blog Django application. It powers blog articles, user accounts, comments, media files, and site settings. By organizing this information in a relational schema, the application can efficiently serve pages, manage user interactions, and support features like post revisions and user roles.

## Tables and Columns

Below is a summary of the main tables. Data types are noted using Django's defaults (e.g., `VARCHAR`, `INTEGER`, `BOOLEAN`). Unless otherwise specified, all tables include an auto-created primary key and timestamp fields.

### `users`
Custom user model storing account and profile information.

- **id** – `UUID` PRIMARY KEY. Unique user identifier.
- **username** – `VARCHAR(150)` UNIQUE NOT NULL. Login name.
- **password** – `VARCHAR(128)` NOT NULL. Hashed password.
- **email** – `VARCHAR(254)` NOT NULL. Contact email.
- **first_name** – `VARCHAR(150)`.
- **last_name** – `VARCHAR(150)`.
- **is_staff** – `BOOLEAN` default `FALSE`.
- **is_active** – `BOOLEAN` default `TRUE`.
- **date_joined** – `DATETIME` default current time.
- **profile_picture_url** – `VARCHAR(200)` optional avatar URL.
- **role** – `VARCHAR(20)` with values `reader` or `author`.
- **status** – `VARCHAR(50)` optional status message.
- **location** – `VARCHAR(100)` optional location text.
- **date_of_birth** – `DATE` nullable.
- **profession** – `VARCHAR(100)` optional profession.
- **interests** – `JSON` list of interests.
- **email_notifications** – `BOOLEAN` default `TRUE`.
- **newsletter_subscription** – `BOOLEAN` default `TRUE`.
- **comment_notifications** – `BOOLEAN` default `TRUE`.
- **marketing_updates** – `BOOLEAN` default `FALSE`.
- **created_at** – `DATETIME` set on creation.
- **updated_at** – `DATETIME` updated on change.

### `blog_contactmessage`
Stores contact form submissions.

- **id** – `INTEGER` PRIMARY KEY.
- **name** – `VARCHAR(255)` NOT NULL.
- **email** – `VARCHAR(254)` NOT NULL.
- **subject** – `VARCHAR(50)` NOT NULL.
- **message** – `TEXT` NOT NULL.
- **agree** – `BOOLEAN` whether sender agreed to terms.
- **created_at** – `DATETIME` set on creation.

### `categories`
Blog post categories with optional hierarchy.

- **id** – `BIGINT` PRIMARY KEY.
- **name** – `VARCHAR(100)`.
- **slug** – `VARCHAR(50)` UNIQUE NOT NULL.
- **description** – `TEXT` optional.
- **parent_category_id** – `BIGINT` nullable FK to `categories.id`.
- **created_at** – `DATETIME`.
- **updated_at** – `DATETIME`.

### `tags`
Simple tag records used for post categorization.

- **id** – `BIGINT` PRIMARY KEY.
- **name** – `VARCHAR(50)`.
- **slug** – `VARCHAR(50)` UNIQUE NOT NULL.
- **created_at** – `DATETIME`.
- **updated_at** – `DATETIME`.

### `posts`
Main table for blog articles.

- **id** – `BIGINT` PRIMARY KEY.
- **author_id** – FK to `users.id`.
- **title** – `VARCHAR(255)`.
- **slug** – `VARCHAR(50)` UNIQUE NOT NULL.
- **content** – `TEXT` full post body.
- **excerpt** – `TEXT` optional summary.
- **featured_image_url** – `VARCHAR(200)` optional image.
- **status** – `VARCHAR(20)` with values `draft` or `published`.
- **published_at** – `DATETIME` nullable when published.
- **created_at** – `DATETIME`.
- **updated_at** – `DATETIME`.
- **view_count** – `INTEGER` UNSIGNED default `0`.
- **seo_title** – `VARCHAR(255)` optional SEO title.
- **meta_description** – `TEXT` optional SEO description.

The `posts` table has many‑to‑many relationships via:
- `posts_categories` linking posts to categories.
- `posts_tags` linking posts to tags.
- `posts_liked_by` linking users who like a post.
- `posts_saved_by` linking users who saved a post.
- `user_saved_posts` logging when a reader saved a post.

### `comments`
User comments on posts.

- **id** – `BIGINT` PRIMARY KEY.
- **post_id** – FK to `posts.id`.
- **user_id** – nullable FK to `users.id`.
- **author_name** – `VARCHAR(255)` optional name when anonymous.
- **author_email** – `VARCHAR(254)` optional email when anonymous.
- **content** – `TEXT` comment body.
- **parent_comment_id** – nullable FK to `comments.id` for threading.
- **status** – `VARCHAR(20)` (`pending`, `approved`, `spam`).
- **created_at** – `DATETIME`.
- **updated_at** – `DATETIME`.
- **ip_address** – `INET` optional stored IP.

### `user_saved_posts`
Tracks when a reader saves an article.

- **id** – `BIGINT` PRIMARY KEY.
- **user_id** – FK to `users.id`.
- **post_id** – FK to `posts.id`.
- **saved_at** – `DATETIME` timestamp when saved.
- **is_active** – `BOOLEAN` flag for soft deletion.

### `media`
Metadata for uploaded media files.

- **id** – `BIGINT` PRIMARY KEY.
- **file_url** – `VARCHAR(200)` pointing to storage.
- **uploaded_at** – `DATETIME`.
- **uploaded_by_id** – nullable FK to `users.id`.
- **post_id** – nullable FK to `posts.id`.

### `post_revisions`
Tracks historical versions of posts.

- **id** – `BIGINT` PRIMARY KEY.
- **post_id** – FK to `posts.id`.
- **content** – `TEXT` revision body.
- **created_at** – `DATETIME`.
- **created_by_id** – nullable FK to `users.id`.
- **version_number** – `INTEGER` NOT NULL.

### `settings`
Simple key-value table for site configuration.

- **id** – `BIGINT` PRIMARY KEY.
- **key** – `VARCHAR(100)` UNIQUE NOT NULL.
- **value** – `TEXT` NOT NULL.
- **description** – `TEXT` optional description.

## Indexes
Important indexes generated by migrations include:

- Unique indexes on `users.username`, `categories.slug`, `tags.slug`, `posts.slug`, and `settings.key` to enforce uniqueness.
- Foreign key indexes such as `categories_parent_category_id`, `posts_author_id`, `media_post_id`, `media_uploaded_by_id`, `comments_post_id`, `comments_user_id`, `comments_parent_comment_id`, `post_revisions_post_id`, and `post_revisions_created_by_id` to speed up joins.
- Many-to-many tables (`posts_categories`, `posts_tags`, `posts_liked_by`, `posts_saved_by`, `users_groups`, `users_user_permissions`) have composite unique indexes on their pairing columns and individual indexes for each foreign key.
- The `user_saved_posts` table has a unique index on `(user_id, post_id)`.

## Keys and Relationships

- Every table uses a primary key (`id`).
- `posts.author_id` → `users.id` (CASCADE on delete)
- `categories.parent_category_id` → `categories.id` (SET NULL on delete)
- `comments.post_id` → `posts.id` (CASCADE)
- `comments.user_id` → `users.id` (SET NULL)
- `comments.parent_comment_id` → `comments.id` (CASCADE)
- `media.post_id` → `posts.id` (CASCADE)
- `media.uploaded_by_id` → `users.id` (SET NULL)
- `post_revisions.post_id` → `posts.id` (CASCADE)
- `post_revisions.created_by_id` → `users.id` (SET NULL)
- Many‑to‑many tables reference their parent tables with ON DELETE CASCADE.
- `user_saved_posts.user_id` → `users.id` (CASCADE)
- `user_saved_posts.post_id` → `posts.id` (CASCADE)

## Stored Procedures and Triggers

The project does not define database-level stored procedures or triggers. Business logic is implemented in the Django application layer.

## User Roles and Permissions

No custom database roles are defined in this repository. Application roles are modeled with the `users.role` column (`reader` or `author`). Database access is typically managed through Django's settings using a single application user.


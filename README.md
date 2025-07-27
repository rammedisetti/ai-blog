# AI Blog

A simple Django-based blog project.

## Blog Page

The site now includes a responsive blog index at `/blog/` showcasing example
articles. The page reuses the landing page header and footer for consistency and
includes a hero section, search bar, category chips, article cards, sidebar,
pagination and a newsletter sign-up.

## Template Structure

All main blog pages extend `blog/base.html` which contains the shared header,
footer and scripts. When creating new templates in the `blog` app, start with:

```django
{% extends "blog/base.html" %}
{% block title %}Page title{% endblock %}
{% block content %}
    <!-- Page content here -->
{% endblock %}
```

Optional CSS or JavaScript can be injected using the `extra_css` and
`extra_js` blocks.

## Signup Feature

The project now includes a minimal signup page where users can create an account
with a unique username and email. Passwords are validated using Django's default
password validators and are securely hashed.

## Login Feature

A lightweight login page lets existing users sign in with their username or
email address and password. After authenticating, users are redirected to the
homepage.

## User Dashboard

Authenticated users now have access to a dashboard at `/user_dashboard/`. The page
uses a two column layout with a sidebar showing the avatar and navigation links.
Users can update their profile information, manage notification preferences and
change their password. A list of the user's own articles is also available.

## Rich Text Editing

The post creation form now integrates **CKEditor** for the `content` field. All
static files are provided via `django-ckeditor` and loaded using `{{ form.media }}` in
`add_post.html`. The default toolbar is enabled and copy-paste from Word is
supported. When adding content, images and rich formatting will be saved
correctly to the `Post` model's `RichTextField`.

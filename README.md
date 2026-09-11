# Music Library

## About This Project

**Music Library** is a feature-rich, responsive web application built with Python and Django. It is designed to help users manage, organize, and explore their personal music collection. 

Key features include:
- **Comprehensive Library Management:** Store and manage detailed information about your favorite Albums and Artists.
- **External API Integrations:** Seamlessly search and import high-quality metadata, album covers, and artist biographies using integrations with the **MusicBrainz** and **TheAudioDB** APIs.
- **Advanced Filtering & Sorting:** Easily find what you are looking for by grouping albums by artist, sorting by release year or title, and filtering by physical format (Vinyl, CD, Digital, etc.).
- **Modern User Interface:** A highly customized, responsive front-end featuring dynamic Grid and List views, pagination, and a built-in Light/Dark mode toggle.
- **CSV Data Import:** Quickly bulk-upload your existing music collection through a CSV upload tool.
- **User Ratings & Authentication:** Create an account to securely save your library and rate your favorite albums and artists.


---

## Project File Structure

```text
uni-musiclib-project/
├── manage.py                  # Standard Django entrypoint
├── pyproject.toml / uv.lock   # Dependencies and virtual environment manager (uv)
├── db.sqlite3                 # Local SQLite database
├── README.md                  # This file
│
├── core/                      # Global Django project settings
│   ├── settings.py            # General configuration, database, installed apps
│   ├── urls.py                # Main routes and inclusion of library/
│   ├── wsgi.py / asgi.py      # Server entrypoints
│   └── __init__.py
│
├── library/                   # The main Django app of the project
│   ├── models.py              # Database models (Artist, Album, Song, etc.)
│   ├── views.py               # Logic and class-based views
│   ├── forms.py               # ModelForms for interactions with models
│   ├── urls.py                # App-specific routes
│   ├── admin.py               # Model registration for the admin panel
│   ├── tests.py               # Automated tests
│   │
│   ├── static/                # Static files
│   │   ├── css/style.css      # Custom CSS stylesheet
│   │   └── scripts/main.js    # JavaScript files (e.g., for interactions)
│   │
│   └── templates/library/     # HTML templates for the app
│       ├── base.html                       # Base template inherited by others
│       ├── _album_card.html                # Reusable partial: album card component
│       ├── _star_rating.html               # Reusable partial: star rating widget
│       ├── album_list.html                 # Album list view
│       ├── album_detail.html               # Album detail page
│       ├── album_form.html                 # Create / edit album form
│       ├── album_confirm_delete.html       # Album delete confirmation
│       ├── artista_list.html               # Artist list view
│       ├── artista_detail.html             # Artist detail page
│       ├── artista_form.html               # Create / edit artist form
│       ├── artista_confirm_delete.html     # Artist delete confirmation
│       ├── artista_metadata.html           # Artist key-value metadata editor
│       ├── canzone_detail.html             # Song detail page
│       ├── canzone_form.html               # Create / edit song form
│       ├── search.html                     # Main search view
│       ├── musicbrainz_search.html         # MusicBrainz external API search
│       ├── theaudiodb_search.html          # TheAudioDB external API search
│       ├── csv_upload.html                 # Bulk upload via CSV
│       ├── profile.html                    # User profile page
│       ├── login.html                      # Login page
│       ├── register.html                   # Registration page
│       ├── admin_users.html                # Admin: user management
│       └── admin_password_change.html      # Admin: password change
│
└── media/                     # Files uploaded by users at runtime
    ├── album/                 # Album covers
    └── artisti/               # Artist profile images
```

---

## Database Structure

[View the interactive Entity-Relationship diagram on Mermaid Live](https://mermaid.live/edit#pako:eNq9VttO20AQ_ZXVSpVACpQQQojfUggV4hIECQ8okjWxJ8609q67XqeUhH_pY_-DH-s6ELDjDVhIrZ_snTmzZ8_MznjGPekjdziqI4JAQTRUQ8HM8-kTu8IQ7kkKYgONQuPSNLjuXrH5fGtrPl-8u5dXveOTsy5z2JBPgG3UnfrmkJfc5Yx1rvon1_3OwpNEgooSDz8HmOjsJUNerEOefRmcfwB30-v33Py2mMSKogqYlw2rIg47F7e9i-46TE7Zr6hAeRMCdp4m5EH4ou2SaenUcToahcZ1lcWTx7N7noEnhSYU6yicowYfNLGNS9AalWDdzs3mGhrn3X7nqLMi5OMf5mPiKdJaMr9EbMllNUSeYy4ErITI1yF5mNUhshupaQ3FUp6VQU3xTblW8mxHrJyjlOkyKkf9CMck6Il81-RDP_5myDpaKxqlr2dZlNJs-ZU9JDQjn12e5hcTAxMBS039C4jQYsIIKLSsx5AkP6XyLaYxqUS7a-KFYLGZskGdFXf24n6TJPAl8ENegEJzqHw8mIIGtdbgpipcDZUp4pp4x6cmIYPT1-QV6CyrozITIYsH13in2Yik6ZNjAguAoggCI4cbKzmmUK7naSe4KMXK9Ew5yfIeIIR008QjbWPoyRiVJmGzjaWKQEt3TKYnSeuGsXQVhghJQZeRlCHzKTBbhuiC9yOlRJtIJWpmZ2MoKlBRm-WVe1-dbFGkESrpagWeZ81UWbuR4W-QfqqgqNwi69qMGps7hKM0eoN2qXNWzm42Hqa2OzmFUCq0cbHJa2dTXc0Ps_FA3Ju29wabQst-n4mPHkUQsjg1_yJBQOXbtfhLKVdXZXly8-A_0HmncgqD5t_TsaeL13igyOeOVinWuLlUZsCYTz7LHIZcT9C0SJ7NQR_Ud9N4RYaJQdxKGS1hSqbBhDtjCBPzlcbZ3Hj-3XxxQeGjOpSGPXcO9huLGNyZ8TvuNPaa2-3GwUGrsduu79Sb-zX-izt7LbPYau609nfbjfZes_FQ4_eLTXe2D8y6eertnd12s9VuPfwFrUhQDg)

The project is based on several main tables (models):

- **User & UserProfile**: Handle user authentication and store their avatar (with a fallback to Gravatar).
- **Artista (Artist)**: Collects data for artists saved by the user (name, biography, profile picture).
- **Album**: Saves the release details (title, release year, physical/digital format) linking them to their `Artista`.
- **Canzone (Song)**: Represents the individual music tracks (with duration and track number) belonging to an `Album`.
- **MetadatoArtista / MetadatoCanzone**: Key-value tables to allow the addition of infinite flexible properties (e.g., "Role: Singer", "Instrument: Guitar").
- **VotoAlbum / VotoArtista / VotoCanzone**: Handle reviews and ratings (from 0.5 to 5 stars) assigned by the user.

---

## Installation & Setup

This project uses [uv](https://github.com/astral-sh/uv), an extremely fast Python package and project manager. 

### Prerequisites
- **Python:** version `>= 3.14`
- **uv:** Follow the [uv installation guide](https://docs.astral.sh/uv/getting-started/installation/) if you don't have it installed on your system.

### Dependencies
The project relies on the following main Python libraries (automatically managed by `uv`):
- `Django >= 6.1.1` (Web framework)
- `Pillow >= 11.0.0` (Image processing for covers/avatars)
- `requests >= 2.32.0` (For external API calls to MusicBrainz/TheAudioDB)

### Step-by-step Guide

1. **Clone the repository**
   Open your terminal and clone the project to your local machine:
   ```bash
   git clone https://github.com/itsmrma/uni-musiclib-project
   cd uni-musiclib-project
   ```

2. **Install dependencies with `uv`**
   Run the following command to automatically create a virtual environment and install all required dependencies listed in the `pyproject.toml` and `uv.lock` files:
   ```bash
   uv sync
   ```

3. **Apply Database Migrations**
   Initialize the SQLite database by running the Django migrations:
   ```bash
   uv run manage.py migrate
   ```

4. **Create a Superuser (Optional but recommended)**
   To access the Django admin panel and have full permissions, create an admin account:
   ```bash
   uv run manage.py createsuperuser
   ```

5. **Start the Development Server**
   Launch the local web server:
   ```bash
   uv run manage.py runserver
   ```

6. **Test it on your PC**
   Open your favorite web browser and navigate to:
   [http://127.0.0.1:8000/](http://127.0.0.1:8000/)

   You can now create an account, log in, and start adding music to your new library!

---
*This is a university project developed for UNIMORE (Università degli Studi di Modena e Reggio Emilia).*

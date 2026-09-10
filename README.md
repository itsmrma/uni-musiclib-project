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

## Struttura del Database

Il progetto è basato su diverse tabelle (modelli) principali:

- **User & UserProfile**: Gestiscono l'autenticazione degli utenti e memorizzano il loro avatar (con fallback a Gravatar).
- **Artista**: Raccoglie i dati degli artisti salvati dall'utente (nome, biografia, foto profilo).
- **Album**: Salva i dettagli delle release (titolo, anno di uscita, formato fisico/digitale) collegandoli al proprio `Artista`.
- **Canzone**: Rappresenta le singole tracce musicali (con durata e numero traccia) appartenenti a un `Album`.
- **MetadatoArtista / MetadatoCanzone**: Tabelle chiave-valore per permettere l'aggiunta di infinite proprietà flessibili (es. "Ruolo: Cantante", "Strumento: Chitarra").
- **VotoAlbum / VotoArtista / VotoCanzone**: Gestiscono le recensioni e i rating (da 0.5 a 5 stelle) assegnati dall'utente.

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

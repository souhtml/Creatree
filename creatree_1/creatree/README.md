# Creatree 🌳

All your links, growing from one root. A free, self-hostable Linktree-style
site: users sign up, add their links, and share one page — `creatree.com/username`.

## Features

- Email + username signup/login (passwords hashed with Werkzeug)
- Public profile page at `/profile/<username>`
- Dashboard to add, delete, and drag-to-reorder links
- Per-link click tracking (every link goes through `/l/<id>` before redirecting)
- Clean, responsive design — no framework, no build step

## Project structure

```
creatree/
├── app.py                 # Flask app: routes, models, auth
├── requirements.txt
├── templates/
│   ├── base.html
│   ├── index.html          # Marketing homepage
│   ├── signup.html
│   ├── login.html
│   ├── dashboard.html      # Logged-in editor
│   └── profile.html        # Public /username page
└── static/
    ├── css/style.css
    └── js/app.js            # Drag-to-reorder
```

## Run it locally

```bash
cd creatree
python3 -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
python app.py
```

Visit `http://localhost:5000`. The SQLite database (`creatree.db`) is created
automatically on first run.

## Deploying for free

### Option A: Render.com
1. Push this folder to a GitHub repo.
2. On Render, create a new **Web Service** from that repo.
3. Build command: `pip install -r requirements.txt`
4. Start command: `gunicorn app:app`
5. Add an environment variable `SECRET_KEY` set to a random string.
6. Deploy — you'll get a free `yourapp.onrender.com` URL.

### Option B: PythonAnywhere
1. Upload the project (or clone from GitHub) in a Bash console.
2. Create a virtualenv and `pip install -r requirements.txt` inside it.
3. In the **Web** tab, create a new Flask app pointing at `app.py`.
4. Set the virtualenv path and reload.

### Custom domain
Both platforms let you attach a custom domain on their free/low tiers later
(e.g. via Freenom or a cheap registrar) once you're ready to move off the
default subdomain.

## Notes on scaling this up

- **Database**: SQLite is fine to start. For multiple concurrent users in
  production, switch `DATABASE_URL` to a free Postgres instance (Render and
  Supabase both offer one) — no code changes needed since SQLAlchemy
  abstracts this.
- **Avatars**: currently just a URL field. For real uploads, add a file
  upload endpoint and store images in something like Cloudinary's free tier.
- **Security**: change `SECRET_KEY` to a long random value in production
  (set it as an environment variable, never commit it).

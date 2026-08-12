# BizBuddy — Single URL Deploy

One Docker service. One public link. Everything works.

| Path | App |
|------|-----|
| `https://YOUR-APP/` | Mart1 React (inventory & billing UI) |
| `https://YOUR-APP/api/` | Mart1 FastAPI backend |
| `https://YOUR-APP/supermarket/` | Supermarket Flask analytics |

Uses your existing **Supabase** database (set `DATABASE_URL`).

---

## 1. One-time: schema on Supabase

If tables are not created yet:

```bash
# Locally, with DATABASE_URL pointing at Supabase
cd mart1
python init_db.py
```

Or paste `mart1/schema[1].sql` into the Supabase SQL Editor and run it.

---

## 2. Push code to GitHub

```bash
cd Bizbuddy
git add Dockerfile deploy/ .dockerignore render.yaml supermarket/wsgi_subdir.py DEPLOY.md
git add -u
git status   # confirm .env is NOT listed
git commit -m "Single-container deploy for Mart1 + Supermarket"
git push
```

---

## 3. Deploy on Render (one service)

### Option A — Blueprint (uses `render.yaml`)

1. [dashboard.render.com](https://dashboard.render.com) → **New** → **Blueprint**
2. Connect the GitHub repo
3. Apply
4. Open the **bizbuddy** service → **Environment**
5. Set:

| Key | Value |
|-----|--------|
| `DATABASE_URL` | Your full Supabase URI (include password + `?sslmode=require`) |
| `FRONTEND_URL` | `https://YOUR-SERVICE.onrender.com` (set after first deploy, then restart) |

### Option B — Manual Web Service

1. **New** → **Web Service** → connect repo  
2. **Runtime:** Docker  
3. **Dockerfile path:** `./Dockerfile`  
4. **Docker context:** `.`  
5. Same env vars as above  

Wait for the build (Node builds the frontend, then Python image). First build can take several minutes.

---

## 4. Open the link

After deploy succeeds:

- **Mart1 UI:** `https://YOUR-SERVICE.onrender.com/`
- Login: `alicej` / `admin123` (or your seed users)
- **API:** `https://YOUR-SERVICE.onrender.com/api/` (e.g. docs if enabled)
- **Supermarket:** `https://YOUR-SERVICE.onrender.com/supermarket/`

---

## Local test with Docker (optional)

```bash
# From Bizbuddy root — requires Docker
export DATABASE_URL="postgresql://...your-supabase..."
docker build -t bizbuddy .
docker run --rm -p 10000:10000 -e DATABASE_URL -e SESSION_SECRET=dev bizbuddy
# Open http://localhost:10000
```

---

## Notes

- **Free Render** spins down after idle; first request may be slow (~30–60s cold start).
- Do **not** commit `.env`. Secrets only in Render Environment.
- Streamlit is not included in this single container (heavier). Use Streamlit Cloud separately if needed.
- Same-origin frontend uses `VITE_API_URL=/api` baked at image build time — no extra frontend env on Render.

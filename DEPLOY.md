# 🚀 Putting AI Debate Coach online (free)

At the end you'll have a link like **https://ai-debate-coach.streamlit.app** that anyone can open on their phone,
create an account, and debate. **No terminal needed** — everything happens on websites.

## The big picture

```
 Phone / laptop  ──▶  Website (Streamlit Cloud)  ──▶  Backend (Render)  ──▶  Online AI (Groq)
                                                          │
                                                          └──▶  Database (Neon) - keeps accounts & history
```

| Service | What it does for you | Cost |
|---|---|---|
| **GitHub** | Stores your code so the other services can read it | Free |
| **Groq** | The AI opponent (online) | Free plan |
| **Neon** | Online database that keeps accounts and history safe | Free plan |
| **Render** | Runs the backend (FastAPI) | Free plan |
| **Streamlit Community Cloud** | Runs the website people visit | Free |

> 💡 Tip: open Notepad and keep it open. You'll copy 3 things into it along the way: your **Groq key**, your **Neon link**, and your **Render link**.

---

## Step 1 — Put the code on GitHub (≈5 min)

1. Go to **github.com** and sign up / log in.
2. Click the **+** (top right) → **New repository**.
3. Name: `ai-debate-coach` · choose **Public** · click **Create repository**.
   *(Public is fine — there are no passwords or keys in the code.)*
4. On the next page click the link **"uploading an existing file"**.
5. Unzip **ai-debate-coach-github.zip**, open the folder, select **everything inside** (Ctrl + A) and drag it into the GitHub page.
6. Wait until every file is listed, then click **Commit changes**.

✅ You should see folders `backend`, `frontend`, `docs`, `tests` on your repository page.

---

## Step 2 — Get your free Groq AI key (≈3 min)

1. Go to **console.groq.com** and sign up / log in.
2. Click **API Keys** → **Create API Key** → give it any name (e.g. `debate-coach`).
3. **Copy the key** (it starts with `gsk_`) and paste it into Notepad.
   ⚠️ It's shown only once. Never post it anywhere or put it in your code.

---

## Step 3 — Create the free database on Neon (≈3 min)

1. Go to **neon.com** and sign up / log in (you can use your GitHub account).
2. Create a project: name `ai-debate-coach`, pick the region closest to Nigeria (e.g. **Europe – Frankfurt**).
3. On the project dashboard click **Connect**.
4. Copy the **connection string** — it looks like
   `postgresql://neondb_owner:xxxx@ep-xxxx.eu-central-1.aws.neon.tech/neondb?sslmode=require`
   and paste it into Notepad.

You don't need to create any tables — the app does that by itself on first start.

---

## Step 4 — Put the backend on Render (≈10 min)

1. Go to **render.com** → **Get Started** → sign in **with GitHub**.
2. Click **+ New** → **Web Service** → pick your `ai-debate-coach` repository (click **Configure GitHub** if it's not listed and allow access).
3. Fill in exactly:

| Field | Type this |
|---|---|
| Name | `ai-debate-coach-api` |
| Root Directory | `backend` |
| Runtime / Language | `Python 3` |
| Build Command | `pip install -r requirements.txt` |
| Start Command | `uvicorn main:app --host 0.0.0.0 --port $PORT` |
| Instance Type | **Free** |

4. Scroll to **Environment Variables** → **Add Environment Variable** twice:

| Key | Value |
|---|---|
| `GROQ_API_KEY` | your Groq key from Notepad |
| `DATABASE_URL` | your Neon connection string from Notepad |

5. Click **Deploy Web Service**. Wait for the green **Live** badge (3–8 minutes the first time).
6. Copy your backend link at the top (like `https://ai-debate-coach-api.onrender.com`) into Notepad.

✅ **Check it:** open `https://YOUR-RENDER-LINK/health` in your browser. You should see `"ai_mode":"online"`.
If it says `"offline"`, the Groq key is missing or wrong (fix it under **Environment** in Render).

---

## Step 5 — Put the website on Streamlit Community Cloud (≈5 min)

1. Go to **share.streamlit.io** → sign in **with GitHub**.
2. Click **Create app** → **Deploy a public app from GitHub**.
3. Fill in:

| Field | Value |
|---|---|
| Repository | `your-github-name/ai-debate-coach` |
| Branch | `main` |
| Main file path | `frontend/app.py` |
| App URL | choose a nice name, e.g. `ai-debate-coach` → gives `ai-debate-coach.streamlit.app` |

4. Click **Advanced settings**:
   - Python version: **3.12**
   - **Secrets** box — paste this one line, with your Render link:
     ```
     BACKEND_URL = "https://ai-debate-coach-api.onrender.com"
     ```
5. Click **Deploy**. Wait for the app to load (2–5 minutes).

🎉 **That's your public link.** Open it on your phone, create an account and start a debate.
The sidebar should say **"AI engine: Online AI ✨"**.

---

## Good to know

| Thing | What happens | What to do |
|---|---|---|
| **First visit after a quiet spell** | Render's free server sleeps after 15 minutes with no visitors. The first login can take up to a minute while it wakes. | Nothing — it's normal. Open the link a minute before you demo it. |
| **Website asleep** | Streamlit sleeps after 12 hours with no visitors and shows a "wake up" button. | Click the button; it's back in under a minute. |
| **Groq daily limit reached** | The app quietly switches to the Offline Brain until the limit resets. | Nothing. Heavy use? Check your limits on console.groq.com. |
| **Changing the code later** | Upload the changed files to GitHub again (same "Add file → Upload files" button). | Render and Streamlit update themselves automatically in a few minutes. |
| **Key accidentally shared** | Someone could use your Groq quota. | Delete the key on console.groq.com, create a new one, paste it into Render → Environment. |

## Something went wrong?

| Problem | Fix |
|---|---|
| Website says **"Can't reach the backend"** | Check the `BACKEND_URL` secret in Streamlit (Settings → Secrets) — it must be your Render link, in quotes, with no `/` at the end. |
| Render build **failed** | Open the **Logs** tab in Render, copy the red lines and send them to Claude. |
| Accounts disappear after a while | `DATABASE_URL` is missing on Render, so it's using a temporary file. Add it under Environment. |
| `/health` shows `"offline"` | `GROQ_API_KEY` missing or mistyped on Render. |

# IdeaVault — Setup Guide

A private, single-user website-idea dashboard using plain HTML, Supabase, GitHub, and Cloudflare Pages.

## Included files

- `index.html` — complete responsive website
- `supabase.sql` — database table, indexes, trigger, grants, and RLS policies

## 1. Run the SQL

1. Open your Supabase project.
2. Go to **SQL Editor**.
3. Create a new query.
4. Copy all contents of `supabase.sql`.
5. Click **Run**.

## 2. Create the only login account

Do not put the password inside `index.html` or SQL.

1. In Supabase, go to **Authentication > Users**.
2. Click **Add user** or **Create new user**.
3. Use:
   - Email: `dhruvp246@gmail.com`
   - Password: the password you selected
4. Mark the email as confirmed / auto-confirm the user when creating it.

The login page already prefills the allowed email, but never prefills or stores the password.

## 3. Disable public signup

In **Authentication settings**, disable new user signups. Keep Email/Password sign-in enabled. There is no signup button in the website, but disabling signup at the Supabase project level gives stronger protection.

## 4. Test locally

Opening the file directly may work, but a local web server is more reliable.

With Python installed, run this inside the project folder:

```bash
python -m http.server 8080
```

Then open:

```text
http://localhost:8080
```

## 5. Upload to GitHub

Create a repository and upload both `index.html` and `supabase.sql`. A public repository is acceptable because the anon key is designed for browser apps; the protection comes from Auth and Row Level Security. Never commit a Supabase secret/service-role key or your password.

Git commands:

```bash
git init
git add .
git commit -m "Create private ideas dashboard"
git branch -M main
git remote add origin https://github.com/YOUR_USERNAME/YOUR_REPOSITORY.git
git push -u origin main
```

## 6. Host on Cloudflare Pages

1. Open Cloudflare.
2. Go to **Workers & Pages**.
3. Select **Create application > Pages > Connect to Git**.
4. Select the GitHub repository.
5. Production branch: `main`.
6. Build command: `exit 0`.
7. Build output directory: `/` or the directory containing `index.html`.
8. Deploy.

Cloudflare should serve the top-level `index.html` automatically.

## Main features

- Secure email/password login
- No signup page
- Restricted to one email in both frontend and database policies
- Create, edit, delete, search, filter, and sort ideas
- Statuses: Planning, Building, Launched, Paused
- Priority, category, target user, tech stack, links, notes, next step, and target date
- Mobile-responsive layout
- Session persistence and logout
- Supabase RLS protection

## Important security notes

- The Supabase anon key is visible by design in a browser application.
- The Supabase secret/service-role key must never be put in this project.
- Never hardcode the login password in HTML, JavaScript, GitHub, or SQL.
- Change the password if it has been shared somewhere you do not trust.

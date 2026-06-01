# Notion Blog (Notion → Jekyll → GitHub Pages)

Write posts in a Notion database; a scheduled GitHub Action pulls them as
Markdown, commits them to this repo, and deploys the Jekyll site to GitHub Pages.

```
Notion DB → sync_notion.py (Notion API) → _posts/*.md → git commit
          → Jekyll build → GitHub Pages
```

## 1. Create the Notion database

Create a database with these properties (exact names matter):

| Property    | Type         | Required | Purpose                          |
|-------------|--------------|----------|----------------------------------|
| `Title`     | Title        | yes      | Post title                       |
| `Published` | Checkbox     | yes      | Only checked rows are synced     |
| `Date`      | Date         | no       | Publish date (defaults to today) |
| `Slug`      | Text         | no       | URL slug (derived from title)    |
| `Tags`      | Multi-select | no       | Post tags                        |
| `Summary`   | Text         | no       | SEO description / excerpt        |

## 2. Create a Notion integration

1. Go to <https://www.notion.so/my-integrations> → **New integration**.
2. Copy the **Internal Integration Token** (starts with `secret_` or `ntn_`).
3. Open your database in Notion → `...` menu → **Connections** → add your
   integration so it can read the pages.
4. Copy the **database ID** from the URL:
   `https://notion.so/<workspace>/<DATABASE_ID>?v=...` — the 32-char hex chunk.

## 3. Add repository secrets

In the GitHub repo: **Settings → Secrets and variables → Actions → New secret**:

- `NOTION_TOKEN` — the integration token
- `NOTION_DB_ID` — the database ID

## 4. Enable GitHub Pages

**Settings → Pages → Build and deployment → Source: GitHub Actions.**

## 5. Push this repo

```bash
git remote add origin git@github.com:<you>/<repo>.git
git add -A && git commit -m "init: notion blog" && git push -u origin main
```

The `Sync Notion to Repo` workflow runs on a 30-minute schedule (or trigger it
manually from the **Actions** tab → **Run workflow**). After it commits new
content, the `Build and Deploy` workflow runs automatically and publishes.

> Note: the sync job pushes with the default `GITHUB_TOKEN`, which does not
> trigger `on: push` workflows. That's why deploy also listens on
> `workflow_run` after the sync completes.

## Local development

```bash
# Jekyll site
bundle install
bundle exec jekyll serve     # http://localhost:4000

# Test the sync locally
pip install -r requirements.txt
export NOTION_TOKEN=secret_xxx
export NOTION_DB_ID=xxxxxxxx
python scripts/sync_notion.py
```

## Supported Notion blocks

Paragraph, headings (1–3), bulleted / numbered / to-do lists (nested),
quote, callout, code, divider, image, equation. Inline bold, italic,
strikethrough, inline code, and links are preserved.

## Tuning the schedule

Edit the `cron` in `.github/workflows/sync.yml`. Default is `17,47 * * * *`
(twice an hour). GitHub cron is UTC and best-effort (may lag a few minutes).

# PS5 patch-news RSS tracker

This project checks Google News RSS for PS5 update-related articles about games in `games.json` and publishes `feed.xml` plus a web page on GitHub Pages. **It does not verify actual game version changes, read your installed game list, or guarantee that all patches are detected.**

## Setup
1. Create a **public** GitHub repository named `ps5-rss-tracker` with the `main` branch.
2. Upload **the contents** of this ZIP to the root of the repository, preserving `.github/workflows/publish.yml`.
3. Edit `games.json` in GitHub. Use exact game titles as JSON strings. Save/commit the change.
4. Under **Settings → Pages → Build and deployment**, choose **GitHub Actions** as the source.
5. Under **Actions → Update PS5 RSS**, click **Run workflow** (if needed). Wait for a green run.
6. Open `https://YOUR-USERNAME.github.io/ps5-rss-tracker/feed.xml` in your RSS reader.

Runs every six hours (GitHub scheduling can be delayed). Editing `games.json` also triggers a run. Search results depend on Google's indexing and may contain unrelated articles. Public GitHub Pages makes your game list and feed publicly accessible. No passwords or tokens needed.

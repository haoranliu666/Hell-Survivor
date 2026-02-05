# Hell-Survivor
A top-down survival action game where a hero fights demons in hell.

## Play Online
🎮 **[Play the game in your browser!](https://haoranliu666.github.io/Hell-Survivor/)**

This project is now a **web-native HTML5 Canvas game** deployed directly to GitHub Pages.

## About
Features in the web port:
- Retro-inspired pixel-style visuals
- Browser-native controls and rendering (no Python runtime required)
- Survival loop with enemy waves, healing pickups, and a boss fight

## Controls
- **WASD / Arrow Keys**: Move
- **Space**: Attack
- **R**: Restart
- **P**: Pause

## Run Locally
Because this is a static web app, you can run it with any local web server.

```bash
python -m http.server 8000
```

Then open: `http://localhost:8000`

## GitHub Pages Deployment
Deployment is automated with GitHub Actions using `.github/workflows/deploy-pages.yml`.
On pushes to `main`, the static site is deployed to GitHub Pages.

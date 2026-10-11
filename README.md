# Hayeon Lee — personal website

Jekyll academic website using the Dumbarton theme and the public layout of `yw-ray.github.io`. Production URL: https://hayeon2ya.github.io.

## Content

- `index.md`: introduction.
- `_config.yml`: identity, social links, site URL, and theme settings.
- `_data/education.yml`, `experience.yml`, `honors.yml`, `skills.yml`: profile sections.
- `_data/nav.yml`: navigation.
- `_bibliography/papers.bib`: publications; `selected = {true}` shows an entry on the homepage. Original titles, journals, years, author roles, impact factors, and notes are preserved. Full author lists were not supplied.
- `_layouts/`, `_includes/`, `_sass/`, `css/`: theme and presentation.
- `pages/publications.html`: full publication list.
- `assets/img/avatar/hayeon.jpg`: original profile photo.
- `assets/pdf/HayeonLee_CV.pdf`: original CV PDF, with its design unchanged.

The reference site's ledger, research dashboards, personal assets, and demo content are excluded. The existing ICU application and backend remain; see `ICU_DEPLOYMENT.md`.

## CV synchronization

The separate `hayeon2ya/resume-template-anubhav` repository continues to build `main.pdf` using its existing LaTeX design. `.github/workflows/sync-cv-pdf.yml` downloads it every 30 minutes or on manual dispatch, validates the PDF header, and commits updates to `assets/pdf/HayeonLee_CV.pdf`. All website CV links open that local PDF directly, as in the reference site.

The Pages workflow also runs after successful CV synchronization, so bot commits update the deployed PDF. The deployment build preserves the previous `/cv.pdf` URL. `/cv/`, `/print.html`, and `/publications/` remain compatibility links.

## Build and deployment

```sh
bundle install
bundle exec jekyll build
bundle exec jekyll serve
```

GitHub Actions builds and deploys `master` through `.github/workflows/jekyll.yml`. Repository **Settings → Pages → Source** must be **GitHub Actions**, since `jekyll-scholar` requires this custom build. Local migration does not change remote settings or publish the site.

Dumbarton theme copyright and license are retained in `LICENSE.txt`; the previous theme's license remains in `LICENSE.md`.

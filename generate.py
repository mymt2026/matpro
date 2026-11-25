
import os
import json
import time
from pathlib import Path
from urllib.request import urlopenfor page in range(1, 1
from urllib.parse import urlencode
from datetime import datetime, timezone

API_KEY = os.environ["TMDB_API_KEY"]
BASE_URL = "https://api.themoviedb.org/3"
IMAGE_URL = "https://image.tmdb.org/t/p/original"

def tmdb(endpoint, **params):
    params["api_key"] = API_KEY
    url = f"{BASE_URL}/{endpoint}?{urlencode(params)}"
    try:
        with urlopen(url, timeout=30) as response:
            return json.load(response)
    except Exception:
        raise RuntimeError(
            f"Error consultando TMDB: {endpoint}"
        ) from None

movies = []
seen = set()

for page in range(1, 6):
    results = tmdb(
        "discover/movie",
        language="es-MX",
        sort_by="popularity.desc",
        include_adult="false",
        page=page
    )

    for item in results.get("results", []):
        movie_id = item["id"]

        if movie_id in seen:
            continue

        seen.add(movie_id)

        if not item.get("backdrop_path"):
            continue

        data = tmdb(
            f"movie/{movie_id}",
            language="es-MX",
            append_to_response="translations"
        )

        translations = data.get(
            "translations", {}
        ).get("translations", [])

        title = ""

        for language, country in [
            ("es", "MX"),
            ("en", "US")
        ]:
            for translation in translations:
                if (
                    translation.get("iso_639_1") == language
                    and translation.get("iso_3166_1") == country
                ):
                    title = (
                        translation.get("data", {}).get("title")
                        or ""
                    ).strip()

                    if title:
                        break

            if title:
                break

        if not title:
            english = tmdb(
                f"movie/{movie_id}",
                language="en-US"
            )
            title = english.get("title")

        title = title or data.get("original_title")

        backdrop = data.get("backdrop_path")
        if not backdrop:
            continue

        movies.append({
            "id": movie_id,
            "title": title,
            "year": (data.get("release_date") or "")[:4],
            "release_date": data.get("release_date") or "",
            "genres": [
                g["name"] for g in data.get("genres", [])
            ],
            "runtime": data.get("runtime") or 0,
            "rating": round(data.get("vote_average") or 0, 1),
            "overview": data.get("overview") or "",
            "backdrop": IMAGE_URL + backdrop,
            "countries": [
                c["iso_3166_1"]
                for c in data.get("production_countries", [])
            ]
        })

        print(f"Película agregada: {title}")
        time.sleep(0.15)

if not movies:
    raise RuntimeError("No se encontraron películas")

Path("public").mkdir(exist_ok=True)

catalog = {
    "updated": datetime.now(timezone.utc).isoformat(),
    "movies": movies
}

Path("public/movies.json").write_text(
    json.dumps(catalog, ensure_ascii=False, indent=2),
    encoding="utf-8"
)

print(f"Catálogo generado: {len(movies)} películas")

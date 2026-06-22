import requests
import os

base_url = "https://d37ci6vzurychx.cloudfront.net/trip-data"

for year in [2024, 2025]:
    for month in range(1, 13):
        filename = f"yellow_tripdata_{year}-{month:02d}.parquet"
        url = f"{base_url}/{filename}"
        save_path = f"data/bronze/year={year}/month={month:02d}/{filename}"
        os.makedirs(os.path.dirname(save_path), exist_ok=True)
        print(f"Downloading {filename}...")
        r = requests.get(url)
        if r.status_code == 200:
            with open(save_path, "wb") as f:
                f.write(r.content)
            print(f"  Saved to {save_path}")
        else:
            print(f"  Failed: HTTP {r.status_code}")

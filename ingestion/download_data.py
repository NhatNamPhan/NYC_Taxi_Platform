import requests
import os
from concurrent.futures import ThreadPoolExecutor

base_url = "https://d37ci6vzurychx.cloudfront.net/trip-data"

def download_file(year_month):
    year, month = year_month
    filename = f"yellow_tripdata_{year}-{month:02d}.parquet"
    url = f"{base_url}/{filename}"
    save_path = f"data/bronze/year={year}/month={month:02d}/{filename}"
    
    # Skip if file already exists
    if os.path.exists(save_path):
        print(f"File {filename} already exists, skipping.")
        return

    os.makedirs(os.path.dirname(save_path), exist_ok=True)
    print(f"Downloading {filename}...")
    
    try:
        r = requests.get(url, stream=True)
        if r.status_code == 200:
            with open(save_path, "wb") as f:
                for chunk in r.iter_content(chunk_size=1024 * 1024):  # Stream in 1MB chunks
                    if chunk:
                        f.write(chunk)
            print(f"  -> Saved {filename}")
        else:
            print(f"  -> Failed: HTTP {r.status_code}")
    except Exception as e:
        print(f"  -> Error downloading {filename}: {e}")

if __name__ == "__main__":
    # Generate (year, month) task tuples
    tasks = [(year, month) for year in [2024, 2025] for month in range(1, 13)]
    
    # Download 4 files concurrently
    with ThreadPoolExecutor(max_workers=4) as executor:
        executor.map(download_file, tasks)

import requests
import time
import json
import boto3
import os
from botocore.exceptions import ClientError

S3_BUCKET_NAME = os.getenv("S3_BUCKET_NAME")

def fetch_top_anime():
    """
    Fetches the top anime from the Kitsu open API (fallback since Jikan is down).
    Runs locally as a one-off script, or scheduled.
    """
    print("Fetching top anime from Kitsu API...")
    url = "https://kitsu.io/api/edge/anime"
    catalog = []
    
    # Just fetching a few pages to get a good dataset
    for page in range(0, 5):
        try:
            # Kitsu uses offset-based pagination (limit max 20)
            params = {
                "page[limit]": 20,
                "page[offset]": page * 20,
                "sort": "-averageRating" # Top rated
            }
            response = requests.get(url, params=params)
            if response.status_code == 200:
                data = response.json()
                for item in data.get("data", []):
                    attrs = item.get("attributes", {})
                    # Map Kitsu data to our expected schema
                    catalog.append({
                        "mal_id": int(item.get("id")), # Using Kitsu ID as a stand-in
                        "title": attrs.get("canonicalTitle"),
                        "synopsis": attrs.get("description", ""),
                        "genres": [], # Kitsu requires separate relationship calls for genres, omitting for speed
                        "score": float(attrs.get("averageRating", 0) or 0) / 10.0, # Scale to 1-10
                        "image_url": attrs.get("posterImage", {}).get("original")
                    })
            else:
                print(f"Failed to fetch offset {page * 20}: {response.status_code}")
                break
        except Exception as e:
            print(f"Error: {e}")
            break
            
        time.sleep(0.1)
        
    print(f"Fetched {len(catalog)} anime.")
    return catalog

def upload_catalog_to_s3(catalog: list):
    if not S3_BUCKET_NAME:
        print("S3_BUCKET_NAME environment variable not set. Saving locally instead.")
        os.makedirs('data/raw', exist_ok=True)
        with open('data/raw/anime_catalog.json', 'w') as f:
            json.dump(catalog, f)
        return
        
    s3 = boto3.client('s3')
    try:
        s3.put_object(
            Bucket=S3_BUCKET_NAME,
            Key='anime/catalog.json',
            Body=json.dumps(catalog),
            ContentType='application/json'
        )
        print(f"Successfully uploaded anime catalog to S3 bucket: {S3_BUCKET_NAME}")
    except ClientError as e:
        print(f"Error uploading to S3: {e}")

def get_catalog_from_s3():
    """Loads catalog for inference."""
    if not S3_BUCKET_NAME:
        # Fallback to local
        path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'data', 'raw', 'anime_catalog.json')
        if os.path.exists(path):
            with open(path, 'r') as f:
                return json.load(f)
        return []
        
    s3 = boto3.client('s3')
    try:
        response = s3.get_object(Bucket=S3_BUCKET_NAME, Key='anime/catalog.json')
        return json.loads(response['Body'].read().decode('utf-8'))
    except ClientError as e:
        print(f"Error loading from S3: {e}")
        return []

if __name__ == "__main__":
    catalog = fetch_top_anime()
    upload_catalog_to_s3(catalog)

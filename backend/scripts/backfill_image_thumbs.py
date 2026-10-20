#!/usr/bin/env python3
"""Create public 320px thumbnails for existing product and recipe photos.

Safe to re-run. Skips deliveries/. Does not touch objects already under thumbs/
except to make sure the sibling thumb and the original are public.

Run from the backend directory:
    python scripts/backfill_image_thumbs.py
    python scripts/backfill_image_thumbs.py --dry-run
"""
from __future__ import annotations

import argparse
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from config import Config  # noqa: E402
from google.cloud import storage  # noqa: E402
from utils.catalog_images import CACHE_CONTROL, encode_thumbnail, upload_public  # noqa: E402
from utils.image_urls import thumbnail_object_name  # noqa: E402

PREFIXES = ('products/', 'recipes/')


def _client():
    creds_path = os.environ.get('GOOGLE_APPLICATION_CREDENTIALS')
    if creds_path and os.path.exists(creds_path):
        from google.oauth2 import service_account
        credentials = service_account.Credentials.from_service_account_file(creds_path)
        return storage.Client(credentials=credentials, project=Config.GCS_PROJECT_ID)
    try:
        import google.auth
        from google.auth.transport.requests import Request
        creds, _ = google.auth.default()
        creds.refresh(Request())
        return storage.Client(project=Config.GCS_PROJECT_ID, credentials=creds)
    except Exception:
        # Local gcloud user, same account used for deploys.
        import subprocess
        from google.oauth2.credentials import Credentials
        token = subprocess.check_output(
            ['gcloud', 'auth', 'print-access-token'], text=True
        ).strip()
        return storage.Client(
            project=Config.GCS_PROJECT_ID, credentials=Credentials(token)
        )


def _ensure_cache(blob, dry_run):
    if dry_run:
        return
    if blob.cache_control != CACHE_CONTROL:
        blob.cache_control = CACHE_CONTROL
        blob.patch()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--dry-run', action='store_true')
    args = parser.parse_args()

    client = _client()
    source = client.bucket(Config.GCS_BUCKET_NAME)
    bucket = client.bucket(Config.GCS_CATALOG_BUCKET)
    created = 0
    published = 0
    skipped = 0
    failed = 0

    for prefix in PREFIXES:
        for blob in client.list_blobs(source, prefix=prefix):
            name = blob.name
            if not name or name.endswith('/') or '/thumbs/' in name:
                continue
            thumb_name = thumbnail_object_name(name)
            if not thumb_name:
                skipped += 1
                continue
            dest_original = bucket.blob(name)
            thumb_blob = bucket.blob(thumb_name)
            try:
                if args.dry_run:
                    print(f'would publish {name} and {thumb_name}')
                    created += 1
                else:
                    raw = blob.download_as_bytes()
                    if not dest_original.exists():
                        upload_public(
                            bucket, name, raw,
                            blob.content_type or 'application/octet-stream',
                        )
                        print(f'copied  {name}')
                    if not thumb_blob.exists():
                        upload_public(bucket, thumb_name, encode_thumbnail(raw), 'image/jpeg')
                        print(f'created {thumb_name}')
                        created += 1
                    else:
                        print(f'exists  {thumb_name}')
                    _ensure_cache(dest_original, args.dry_run)
                    _ensure_cache(bucket.blob(thumb_name), args.dry_run)
                published += 1
            except Exception as exc:
                failed += 1
                print(f'FAILED {name}: {exc}', file=sys.stderr)

    print(f'done created={created} published={published} skipped={skipped} failed={failed}')
    if failed:
        sys.exit(1)


if __name__ == '__main__':
    main()

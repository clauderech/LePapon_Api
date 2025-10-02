#!/usr/bin/env python3
"""Send `response.json` to the Lepapon API endpoint.

Usage:
  python send_response_to_api.py --file response.json \
      --url http://lepapon.api/api/ambev/multiple

Optional environment variables:
  LEPAPON_API_TOKEN   : Bearer token to add to Authorization header (optional)

This script will perform up to 3 retries with exponential backoff on 5xx/network errors.
"""
import json
import os
import time
import logging
import argparse
from typing import Any, Dict

import requests

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")


def load_json(path: str) -> Any:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def post_json(url: str, payload: Any, headers: Dict[str, str], retries: int = 3, backoff: float = 1.0):
    attempt = 0
    while True:
        attempt += 1
        try:
            logging.info(f"POST {url} (attempt {attempt})")
            r = requests.post(url, json=payload, headers=headers, timeout=30)
            if 200 <= r.status_code < 300:
                logging.info(f"Success (status {r.status_code})")
                return r
            # do not retry for client errors
            if 400 <= r.status_code < 500:
                logging.error(f"Client error {r.status_code}: {r.text}")
                return r
            # server error -> retry
            logging.warning(f"Server error {r.status_code}, response: {r.text}")
        except requests.RequestException as e:
            logging.warning(f"Network/request error: {e}")

        if attempt >= retries:
            raise RuntimeError(f"Failed after {attempt} attempts")

        sleep_time = backoff * (2 ** (attempt - 1))
        logging.info(f"Retrying in {sleep_time} seconds...")
        time.sleep(sleep_time)


def main():
    parser = argparse.ArgumentParser(description="Send a JSON file or all JSONs in a directory to Lepapon API")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--file", "-f", help="Path to a single JSON file to send")
    group.add_argument("--dir", "-d", help="Directory containing JSON files to send (recursively)")
    parser.add_argument("--url", default="http://lepapon.api/api/ambev/multiple", help="Endpoint URL")
    parser.add_argument("--retries", type=int, default=3, help="Number of retries on failure")
    parser.add_argument("--continue-on-error", action="store_true", help="Continue sending other files if one fails (useful in directory mode)")
    args = parser.parse_args()

    headers = {"Content-Type": "application/json"}
    token = os.getenv("LEPAPON_API_TOKEN")
    if token:
        headers["Authorization"] = f"Bearer {token}"

    def send_single(path: str) -> bool:
        try:
            if not os.path.exists(path):
                logging.error(f"File not found: {path}")
                return False
            payload = load_json(path)
            if not isinstance(payload, dict) or "produtos" not in payload or not isinstance(payload["produtos"], list):
                logging.error(f"Invalid payload in {path}: top-level 'produtos' list required")
                return False

            resp = post_json(args.url, payload, headers, retries=args.retries)
            logging.info(f"{path} -> {resp.status_code}")
            return 200 <= resp.status_code < 300
        except Exception as e:
            logging.error(f"Failed to POST {path}: {e}")
            # save payload for inspection
            try:
                backup = f"{os.path.basename(path)}.failed.json"
                with open(backup, "w", encoding="utf-8") as f:
                    json.dump(load_json(path), f, ensure_ascii=False, indent=2)
                logging.info(f"Payload saved to {backup}")
            except Exception:
                pass
            return False

    if args.file:
        success = send_single(args.file)
        if not success:
            raise SystemExit(1)
    else:
        dirpath = args.dir
        if not os.path.isdir(dirpath):
            logging.error(f"Not a directory: {dirpath}")
            raise SystemExit(2)
        json_files = sorted([p for p in __import__("pathlib").Path(dirpath).rglob("*.json")])
        if not json_files:
            logging.info("No JSON files found in directory")
            return
        failures = []
        for p in json_files:
            ok = send_single(str(p))
            if not ok:
                failures.append(str(p))
                if not args.continue_on_error:
                    logging.error("Stopping due to failure; use --continue-on-error to proceed on errors")
                    raise SystemExit(1)
        logging.info(f"Finished. Total: {len(json_files)}, Failures: {len(failures)}")


if __name__ == "__main__":
    main()

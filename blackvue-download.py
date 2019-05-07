import argparse
import logging
import os
import pathlib
import shutil
import signal
import sys
import time

import requests

WAIT_TIME = 300

logging.basicConfig(
    format='%(asctime)s - %(levelname)-10s - %(message)s',
    level=logging.INFO
)

timeformat = "%Y-%m-%d %H:%M"


def sig_handler(signalnum, frame):
    logging.debug(f"Caught signal {signalnum}: {frame}")
    logging.info("Exiting program.")
    exit()


if __name__ == '__main__':

    logging.info("Running program.")

    signal.signal(signal.SIGTERM, sig_handler)
    signal.signal(signal.SIGINT, sig_handler)

    parser = argparse.ArgumentParser(description="Download files from BlackVue camera")
    parser.add_argument("destination", help="the download directory")
    parser.add_argument("host", help="the IP/hostname of the camera")

    args = parser.parse_args()

    base = "http://" + args.host
    url = f"{base}/blackvue_vod.cgi"

    if not os.path.isdir(args.destination):
        logging.error(f"Destination directory {args.destination} does not exist.")
        sys.exit(1)

    while True:

        logging.debug("Starting run.")

        skipped = 0
        downloaded = 0
        errored = 0

        try:
            logging.info(f"Getting {url}")
            result = requests.get(url, timeout=5)

            if result.status_code > 299:
                raise ValueError(f"{result.status_code} {result.reason}")

            content = result.content.splitlines()
            cam_files = []
            for f in content:
                if "Record" in f.decode():
                    video = f.decode().split(",")[0].split(":")[1]
                    cam_files.append(video)
                    if video.endswith("_NF.mp4"):
                        basename = video[:-5]
                        cam_files.append(basename + ".3gf")
                        cam_files.append(basename + ".gps")

            for f in sorted(cam_files):
                fn = f.split("/")[-1]
                y, m, d = fn[0:4], fn[4:6], fn[6:8]
                dest_dir = os.path.join(args.destination, y, m, d)
                if not os.path.isfile(os.path.join(dest_dir, fn)):
                    dest = os.path.join(args.destination, fn)
                    logging.info(f"Downloading {f} to {dest} ...")
                    try:
                        r = requests.get(base + f, stream=True, timeout=5)
                        with open(dest + ".tmp", 'wb') as f:
                            shutil.copyfileobj(r.raw, f)
                        pathlib.Path(dest_dir).mkdir(parents=True, exist_ok=True)
                        os.rename(dest + ".tmp", os.path.join(dest_dir, fn))

                        downloaded += 1
                    except TimeoutError as rt:
                        logging.error(f"Connection timed out while downloading: {rt}")
                        errored += 1
                else:
                    logging.info(f"File {fn} already downloaded, skipping.")
                    skipped += 1

            logging.info(f"{len(cam_files)} total, {skipped} skipped, {downloaded} downloaded, {errored} errored.")

        except requests.exceptions.ReadTimeout as rt:
            logging.info(f"Connection timeout to {args.host}: {rt}")
        except requests.exceptions.ConnectionError as ce:
            logging.warning(f"Cannot connect to {args.host}: {ce}")
        except ValueError as ve:
            logging.error(ve)

        logging.debug(f"Ending run, waiting {WAIT_TIME} seconds.")
        time.sleep(WAIT_TIME)

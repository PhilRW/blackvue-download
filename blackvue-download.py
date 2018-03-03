import argparse
import logging
import shutil

import os

import pathlib

import requests
import sys

root = logging.getLogger()
root.setLevel(logging.DEBUG)

console = logging.StreamHandler(sys.stdout)
console.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
console.setFormatter(formatter)
root.addHandler(console)

timeformat = "%Y-%m-%d %H:%M"

if __name__ == '__main__':

    logging.info("Starting run")
    parser = argparse.ArgumentParser(description="Download files from BlackVue camera")
    parser.add_argument("host", help="the IP/hostname of the camera")
    parser.add_argument("destination", help="the download directory")

    args = parser.parse_args()

    base = "http://" + args.host
    url = "{0}/blackvue_vod.cgi".format(base)

    if not os.path.isdir(args.destination):
        logging.warning("destination directory {0} does not exist".format(args.destination))
        sys.exit(1)

    try:
        skipped = 0
        downloaded = 0
        errored = 0

        result = requests.get(url)

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
                logging.info("downloading {0} to {1} ...".format(f, dest))
                try:
                    r = requests.get(base + f, stream=True, timeout=5)
                    with open(dest + ".tmp", 'wb') as f:
                        shutil.copyfileobj(r.raw, f)
                    pathlib.Path(dest_dir).mkdir(parents=True, exist_ok=True)
                    os.rename(dest + ".tmp", os.path.join(dest_dir, fn))

                    downloaded += 1
                except TimeoutError as e:
                    logging.error("... connection timed out while downloading: {0}".format(e))
                    errored += 1
            else:
                logging.info("file {0} already downloaded, skipping".format(fn))
                skipped += 1

        logging.info("{0} total, {1} skipped, {2} downloaded, {3} errored".format(len(cam_files), skipped, downloaded, errored))

    except (requests.exceptions.ConnectionError, requests.packages.urllib3.exceptions.ReadTimeoutError) as e:
        logging.error("Problem connecting to host {0}: {1}".format(args.host, e))

    logging.info("ending run")

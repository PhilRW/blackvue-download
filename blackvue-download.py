import argparse
import shutil

import os

import pathlib

import datetime
import requests
import sys

timeformat = "%Y-%m-%d %H:%M"

if __name__ == '__main__':

    print("---=== Starting run at {0} ===---".format(datetime.datetime.now().strftime(timeformat)))
    parser = argparse.ArgumentParser(description="Download files from BlackVue camera")
    parser.add_argument("host", help="the IP/hostname of the camera")
    parser.add_argument("destination", help="the download directory")

    args = parser.parse_args()

    base = "http://" + args.host
    url = "{0}/blackvue_vod.cgi".format(base)

    if not os.path.isdir(args.destination):
        print("destination directory {0} does not exist".format(args.destination))
        sys.exit(1)

    response = os.system("ping -c 1 " + args.host)
    if response != 0:
        print("host {0} is down".format(args.host))
        sys.exit(2)

    try:
        skipped = 0
        downloaded = 0

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
                print("downloading {0} to {1} ...".format(f, dest))
                try:
                    r = requests.get(base + f, stream=True, timeout=5)
                    with open(dest + ".tmp", 'wb') as f:
                        shutil.copyfileobj(r.raw, f)
                    pathlib.Path(dest_dir).mkdir(parents=True, exist_ok=True)
                    os.rename(dest + ".tmp", os.path.join(dest_dir, fn))

                    downloaded += 1
                except requests.exceptions.Timeout as e:
                    print("... connection timed out while downloading: {0}".format(e))
            else:
                print("file {0} already downloaded, skipping".format(fn))
                skipped += 1

        print("{0} total, {1} skipped, {2} downloaded".format(len(cam_files), skipped, downloaded))

    except requests.exceptions.ConnectionError as e:
        print("Problem connecting to host {0}: {1}".format(args.host, e))

    print("---=== ending run at {0} ===---".format(datetime.datetime.now().strftime(timeformat)))

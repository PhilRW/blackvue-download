# blackvue-download
Download video files from BlackVue camera

## How to use
Run the python script and pass it two arguments: the destination directory and the IP/hostname of the camera.

It will run continuously and will wait 5 minutes between trying to reach the host.

```bash
python ./blackvue-download.py /home/me/BlackVue 192.168.0.123 
```

The script will place the files in subfolders based on year, month, and day (YYYY/MM/DD).

You may need to install the requirements first:

```bash
pip install -r requirements.txt
```

## Docker

There is a Docker image available. Simply map a volume where you want it stored and pass the hostname/IP of the camera:

`docker run -v /home/me/BlackVue:/data philrw/blackvue-download 192.168.0.123`

If you don't map the [data volume](https://docs.docker.com/storage/), it will be anonymous.
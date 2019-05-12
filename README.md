## Setup 

If you don't have docker and docker-compose you will need to install them. DO NOT just install the apt versions particularly for docker-compose as they are very outdated. You will need to at least support the docker compose file version 3 spec. 

### Docker

See the [docker CE documentation](https://docs.docker.com/install/linux/docker-ce/ubuntu/#install-using-the-repository) for up-to-date instructions. Example installation:

```
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo apt-key add -
sudo add-apt-repository \
  "deb [arch=amd64] https://download.docker.com/linux/ubuntu \
  $(lsb_release -cs) \
  stable"
sudo apt update
sudo apt install docker-ce
```

`pgrep` docker to make sure the docker daemon is running (it should start automatically)
If it isn't, start it manually (e.g. `systemctl start docker` or `service` or however you want to do it)

### Docker Compose

Check https://docs.docker.com/compose/install/ for the linux install if you want the latest version. Example installation:

```
sudo curl -L "https://github.com/docker/compose/releases/download/1.23.1/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose
```

You will need to add your user to the docker group so you can run it without sudo. 

```
sudo groupadd docker
sudo usermod -aG docker $(whoami)
```

Log out/log back in so the changes take effect. Test your docker setup with `docker run hello-world`.

You might want local sitespeed for test/experimenting/inspecting what happens in the browser when you run your tests. You can simply `npm install sitespeed.io` it. 

## Run tests in docker

First, cd to the same directory as the `docker-compose.yml` file (probably test/perf) and start the sitespeed and graphana containers with `docker-compose up -d`. You will need to edit the configuration file before doing anything else.

Edit `config_template.json` to use the values for your environment/url you want to test. You need to set your own BASE_URL (the base url for the version of reg you want to test) and CONTAINER_IP (the IP for the sitespeed container). You can get the container IP with `docker inspect $(docker ps | grep sitespeedio | sed 's/\s.*//' ) | grep IPAddress\"`

Example:
```
  "BASE_URL": "http://mkoo-ud.dev.oanda.com:9000", # You should replace this
  "CONTAINER_IP": "172.33.0.3", # You should _definitely_ replace this
  "TRIALS_PER_URL": "3"
  ...
```

Once these are set, copy it over: `cp config_template.json config.json` (or just edit the template and save it as config.json)

The script `run_sitespeed.py` should do everything for you. 
- Grab a existing test users' sso tokens
- Run sitespeed on each page and pass the default metrics (namespaced per page) to graphana. 
- If you want to add additional config/flags to your sitespeed run, just append them to the cmd run here.

You can run it manually, put in a cron, etc. Of course the target needs to exist/accept connections, e.g. if you are using your local dev instance your grunt serve/make rundev need to be running on the right port, etc.

## Storage/dashboards

Results will be stored both locally in `sitespeed_results` (with nice html reports), and in the graphana container volume. You can reset the data by removing the graphana volume (`docker volume ls`  then `docker volume rm $VOLUME`). One datapoint will be stored each time `run_sitespeed.py` is run - we will have to decide/configure the downsampled resolution/length of time to store data. 

You will have to do some navigation for the dashboard GUI. Go to `localhost:3000`, find the sign in button in the bottom left sidebar and login with `admin/password`. Then find the dashboards icon icon on the sidebar and click "Manage."The one you probably want to look at is "Page Summary".

The default sitespeed configuration takes 3000+ metrics that we may or may not care for. To view the list:

```
docker run --shm-size=1g --rm -v "$(pwd)":/sitespeed.io sitespeedio/sitespeed.io https://www.sitespeed.io --metrics.filterList
vi $(find sitespeed-results -name *metrics.txt)
```

## Raw data output

Sitespeed has an undocumented plugin that dumps metrics. Run with `--plugins.load analysisstorer"` and `find sitespeed-results -name "*.json"`.

## Troubleshooting

### Timeout errors
If you get timeout errors, make sure you followed the configuration instructions (edit config_template.json and rename it config.json) and that the app at BASE_URL is running.

### Networking

It's possible that the perf_default network used for this will conflict with something. You can change the ip in `docker-compose.yml` under networks > default > ipam > config > subnet.

### Best practice
You can use sitespeed with selenium, but due to selenium's general flakiness/weirdness I would recommend putting together a strategy for component/page/storyboard-level testing if you want more fine-grained control/more targetted measurements than page loads. Using sitespeed together with selenium kind of reduces the value of both tools.

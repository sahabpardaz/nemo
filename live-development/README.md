# Nemo Live Development

To develop Nemo locally and see the live service when changing stuff in backend/frontend, you should read the following instructions.

## Prerequisites
The below instructions are tested with Ubuntu 20.04 and Docker 20.10. You also have to provide python environment like [this Dockerfile](../backend/Dockerfile) and node environment like [this Dockerfile](../frontend/Dockerfile) in your system.

## How To Run
There is a helper script (`bootstrap.sh`) that does all the jobs automatically. Just run it and wait for the final log denoting the backend is up and running. It looks something like this:
```
Starting development server at http://0.0.0.0:8000/
Quit the server with CONTROL-C.

```
Now Nemo is running at *localhost* (port 80) and any change to the **backend** or **frontend** is applied automatically on the fly! (i.e. no need to restart on changes.)  
 
**Note:** If you want to access Nemo by IP (i.e. from another location outside), make sure to also change the `API_URL` config in [AppConfig.js](../frontend/public/AppConfig.js) to point the host IP.

## Example data
If you want to load some initial data, you can do so by the following command (in the `backend` directory):
```bash
python manage.py runscenario <scenario_name>
```
You can find scenario names and their data [here](../backend/apps/dashboard/scenarios)

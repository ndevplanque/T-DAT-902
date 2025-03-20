# T-DAT-902
Homepedia project

## Getting started

### Prerequisites

Create a `.env` file in `/frontend` with:

- `API_V1_URL` : the URL of the backend API

Create a `.env` file in `/backend` with:

- `MAPBOX_ACCESS_TOKEN` : the access token for the mapbox API (generate it [here](https://console.mapbox.com/account/access-tokens/))

### Run the project

Run the following command:

```sh
sh launch.sh
```

Wait until the geo_importer container has finished importing the data.  You can check the logs of the container to see the progress.

As Flask is not good at handling async work, generating the map must be done by hand with this command.  Go the `backend` container and run the following command in Exec tab:

```sh
python3 generate_map.py
```

You can now access the frontend at `http://localhost:3000` and the backend at `http://localhost:5000`.

@Todo : migrate backend to FastAPI to handle async map generation.

## Test the project

### API's Unit Tests

Install the following dependencies:

- `python3.9`
- `pytest`
- `pytest-mock`

Run the following command:

```sh
pytest backend
```

### Data integrity tests

Install the following dependencies:

- `python3.9`
- `folium`
- `psycopg2-binary`
- `shapely`

Run the following command:

```sh
cd geo_importer
python3 test_polygons.py
```

# Members:
- [Thibaut Ruscher](https://github.com/ThibautRuscher)
- [Pierre Halm](https://github.com/Pirooooooo)
- [Nicolas Delplanque](https://github.com/ndevplanque)
- [Safidy Joas](https://github.com/Razanakotoniaina)
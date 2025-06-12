# CLAUDE.md - Homepedia Project Architecture Guide

## Project Overview

Homepedia (T-DAT-902) is a comprehensive real estate data analysis platform that combines geographic data, property sales data, and user reviews to provide insights about French cities and regions. The project uses a microservices architecture with multiple data processing pipelines.

## Architecture Overview

### Core Technologies
- **Backend**: Flask API with Python 3.9
- **Frontend**: Streamlit web application
- **Databases**: PostgreSQL (PostGIS) for geospatial data, MongoDB for reviews
- **Big Data**: Hadoop HDFS + Apache Spark for distributed processing
- **Orchestration**: Docker Compose with 15+ services

### Data Flow
1. **Data Collection**: Scraper collects city reviews from "bien-dans-ma-ville.fr"
2. **Geographic Data**: GeoJSON files imported via Spark into PostgreSQL
3. **Property Data**: CSV property sales data processed via Spark
4. **Text Processing**: Spark processes reviews for sentiment analysis and word clouds
5. **Data Aggregation**: Statistics computed at city, department, and region levels
6. **API & Frontend**: Flask serves processed data to Streamlit dashboard

## Directory Structure

```
/Users/thibruscher/Developer/Epitech/MSc2/T-DAT-902/
├── backend/                 # Flask API
├── frontend/               # Streamlit application
├── avis-scraper/          # Review scraping service
├── avis-processor/        # Review text processing (Spark)
├── data-aggregator/       # Statistical aggregation service
├── geo_importer/          # Geographic data importer (Spark)
├── properties/            # Property sales data processor (Spark)
├── sql/                   # Database schema files
├── documentation/         # Project documentation
├── docker-compose.yml     # Service orchestration
└── launch.sh             # Quick start script
```

## Quick Start Commands

### Basic Operations
```bash
# Start all services
sh launch.sh

# Stop and cleanup
docker compose down --volumes

# View service logs
docker compose logs [service-name]

# Access running containers
docker compose exec [service-name] bash
```

### Service URLs
- Frontend: http://localhost:8501
- Backend API: http://localhost:5001
- PostgreSQL: localhost:5432
- MongoDB: localhost:27017
- Spark Master UI: http://localhost:8080
- Hadoop NameNode UI: http://localhost:9870

## Development Workflows

### Backend Development

**Requirements**: `/Users/thibruscher/Developer/Epitech/MSc2/T-DAT-902/backend/requirements.txt`
- Flask, Flask-CORS, psycopg2-binary, pymongo, pytest, numpy, matplotlib, wordcloud

**Key Files**:
- Main API: `/Users/thibruscher/Developer/Epitech/MSc2/T-DAT-902/backend/api/main.py`
- Configuration: `/Users/thibruscher/Developer/Epitech/MSc2/T-DAT-902/backend/pytest.ini`

**Testing**:
```bash
# Run all tests with coverage
docker compose exec backend pytest

# Run specific test module
docker compose exec backend pytest tests/api/v1/features/health/

# Test with coverage report
docker compose exec backend pytest --cov=api --cov-report=term-missing
```

**API Endpoints**:
- `GET /api/v1/health` - Health check
- `GET /api/v1/map-areas/<zoom>/<sw_lat>/<sw_lon>/<ne_lat>/<ne_lon>` - Geographic areas
- `GET /api/v1/price-tables` - Property price data
- `GET /api/v1/sentiments/<entity>/<id>` - Sentiment analysis
- `GET /api/v1/word-clouds/<entity>/<id>` - Word clouds
- `GET /api/v1/area-details/<entity>/<id>` - Area details

### Frontend Development

**Requirements**: `/Users/thibruscher/Developer/Epitech/MSc2/T-DAT-902/frontend/requirements.txt`
- Streamlit, requests, pandas, python-dotenv

**Configuration**:
Create `/Users/thibruscher/Developer/Epitech/MSc2/T-DAT-902/frontend/.env`:
```
API_URL=http://backend:5001
MAPBOX_ACCESS_TOKEN=your_mapbox_token
```

**Pages**:
- Home: `/Users/thibruscher/Developer/Epitech/MSc2/T-DAT-902/frontend/app/🏠_Homepedia.py`
- Map: `/Users/thibruscher/Developer/Epitech/MSc2/T-DAT-902/frontend/app/pages/1_🌍_Map.py`
- Price Tables: `/Users/thibruscher/Developer/Epitech/MSc2/T-DAT-902/frontend/app/pages/2_💰_Price_Tables.py`

### Data Processing Services

#### Review Scraper
**Location**: `/Users/thibruscher/Developer/Epitech/MSc2/T-DAT-902/avis-scraper/`
**Purpose**: Scrapes city reviews from "bien-dans-ma-ville.fr"

**Environment Variables**:
```
MONGO_URI=mongodb://root:rootpassword@mongodb:27017/
MONGO_DB=villes_france
MAX_VILLES=0  # 0 = all cities
MAX_WORKERS=8  # Parallel threads
ENABLE_SCRAPER=true  # Can use existing dump instead
```

**Validation**:
```bash
docker compose exec avis-data-validator python validate_data.py
```

#### Review Processor (Spark)
**Location**: `/Users/thibruscher/Developer/Epitech/MSc2/T-DAT-902/avis-processor/`
**Purpose**: Sentiment analysis and word cloud generation using Spark

**Submit Job**:
```bash
docker compose exec avis-processor-submitter bash submit.sh
```

**Validation**:
```bash
docker compose exec avis-processor-validator python verify_processing.py
```

#### Data Aggregator
**Location**: `/Users/thibruscher/Developer/Epitech/MSc2/T-DAT-902/data-aggregator/`
**Purpose**: Aggregates statistics by department and region

**Validation Results**: `/Users/thibruscher/Developer/Epitech/MSc2/T-DAT-902/data-aggregator/validation/results/`

#### Geographic Data Importer
**Location**: `/Users/thibruscher/Developer/Epitech/MSc2/T-DAT-902/geo_importer/`
**Purpose**: Imports GeoJSON files (communes, departments, regions) into PostgreSQL

**Test Geographic Data**:
```bash
cd /Users/thibruscher/Developer/Epitech/MSc2/T-DAT-902/geo_importer
python3 test_polygons.py
```

#### Property Data Processor
**Location**: `/Users/thibruscher/Developer/Epitech/MSc2/T-DAT-902/properties/`
**Purpose**: Processes CSV property sales data via Spark

**Submit Job**:
```bash
docker compose exec properties-importer bash spark-submit.sh
```

## Database Schemas

### PostgreSQL Tables
- **regions**: Region geometries and metadata
- **departments**: Department geometries linked to regions
- **cities**: City geometries linked to departments
- **properties**: Property sales data with geospatial coordinates

**Schema Files**:
- `/Users/thibruscher/Developer/Epitech/MSc2/T-DAT-902/sql/create_polygons_tables.sql`
- `/Users/thibruscher/Developer/Epitech/MSc2/T-DAT-902/sql/create_properties_table.sql`

### MongoDB Collections
- **villes**: City information and scraped reviews
- **avis**: Individual reviews with ratings and text
- **mots_villes**: Word frequency data for word clouds
- **departements_stats**: Aggregated department statistics
- **regions_stats**: Aggregated region statistics

## Testing & Validation

### Backend Unit Tests
```bash
# Full test suite
docker compose exec backend pytest

# With coverage
docker compose exec backend pytest --cov=api --cov-report=html

# Specific feature tests
docker compose exec backend pytest tests/api/v1/features/health/
```

### Data Validation Services
Each data processing service has validation containers:

1. **Scraper Validation**: Validates scraped review data quality
2. **Processor Validation**: Verifies sentiment analysis and word clouds
3. **Aggregator Validation**: Checks statistical aggregations
4. **Geographic Validation**: Tests polygon imports and spatial queries

### Validation Results
Check these directories for validation outputs:
- `/Users/thibruscher/Developer/Epitech/MSc2/T-DAT-902/avis-scraper/validation/validation_results.json`
- `/Users/thibruscher/Developer/Epitech/MSc2/T-DAT-902/avis-processor/validation/results/`
- `/Users/thibruscher/Developer/Epitech/MSc2/T-DAT-902/data-aggregator/validation/results/`

## Environment Configuration

### Required Environment Variables
```bash
# MongoDB
MONGO_URI=mongodb://root:rootpassword@mongodb:27017/
MONGO_DB=villes_france

# PostgreSQL
POSTGRES_DB=gis_db
POSTGRES_USER=postgres
POSTGRES_PASSWORD=postgres
POSTGRES_HOST=postgres

# Spark
SPARK_MASTER=spark://spark-master:7077
PYSPARK_PYTHON=/usr/bin/python3.9

# Scraper Configuration
ENABLE_SCRAPER=true
USE_MONGODB_DUMP=false
MAX_VILLES=0
MAX_WORKERS=8
```

### Service Dependencies
The docker-compose.yml defines a complex dependency chain:
1. PostgreSQL, MongoDB (base services)
2. Hadoop (namenode, datanode)
3. Spark (master, workers)
4. Data importers (geo, properties)
5. Scrapers and processors
6. API and frontend

## Common Development Tasks

### Adding New API Endpoints
1. Create service in `/Users/thibruscher/Developer/Epitech/MSc2/T-DAT-902/backend/api/v1/features/`
2. Add repository for data access
3. Register route in `/Users/thibruscher/Developer/Epitech/MSc2/T-DAT-902/backend/api/main.py`
4. Write tests in `/Users/thibruscher/Developer/Epitech/MSc2/T-DAT-902/backend/tests/`

### Adding New Data Processing
1. Create new service directory with Dockerfile
2. Add to docker-compose.yml with dependencies
3. Create validation scripts
4. Add submit scripts for Spark jobs if needed

### Debugging Data Issues
1. Check service logs: `docker compose logs [service-name]`
2. Run validation services to identify data quality issues
3. Use MongoDB/PostgreSQL clients to inspect data directly
4. Check Spark UI for job failures: http://localhost:8080

## Performance Considerations

### Spark Configuration
- 2 Spark workers with 8G RAM each, 4 cores
- Custom JARs for PostgreSQL connectivity
- HDFS for distributed file storage

### Database Optimization
- Spatial indexes on PostGIS geometry columns
- MongoDB indexes on frequently queried fields
- Connection pooling in services

### Scaling
- Add more Spark workers by duplicating worker services
- Increase RAM/CPU allocation in docker-compose.yml
- Use external databases for production deployments

## Troubleshooting

### Common Issues
1. **Service startup failures**: Check dependencies and resource allocation
2. **Spark job failures**: Verify HDFS connectivity and JAR availability
3. **MongoDB connection issues**: Ensure authentication and network access
4. **PostGIS errors**: Check extension installation and table creation

### Debugging Commands
```bash
# Check service health
docker compose ps

# View specific service logs
docker compose logs -f [service-name]

# Access database directly
docker compose exec postgres psql -U postgres -d gis_db
docker compose exec mongodb mongosh --username root --password rootpassword

# Check Spark job status
curl http://localhost:8080/api/v1/applications
```

## Development Best Practices

1. **Always run validation services** after data processing changes
2. **Use the test environment variables** when developing (TEST_MODE=true)
3. **Check logs regularly** for warnings and errors
4. **Backup data** before major changes (MongoDB dumps available)
5. **Test with limited data** first (MAX_VILLES=5 for scraper testing)
6. **Monitor resource usage** - services require significant RAM

This guide should provide future Claude instances with comprehensive understanding of the Homepedia project architecture, development workflows, and common tasks.
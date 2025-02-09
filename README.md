# DOCKER-GUI


## How to build

```bash
docker-compose down -v; CACHE_BREAKER=$(date +%s) SHARED_DIR=log docker-compose up --build
```
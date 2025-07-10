.PHONY: all build up down clean test rebuild logs ps add rep

# Default target: build and run
all: build up

# Regular build (cached)
build:
	docker-compose build

# Start containers
up:
	docker-compose up -d

# Stop containers
down:
	docker-compose down

# Clean everything including volumes and unused images
clean:
	docker-compose down -v
	docker system prune -f

# Force rebuild everything (no cache, fresh code)
rebuild:
	docker-compose down
	docker image rm -f loadbalancingproject-load_balancer || true
	docker-compose build --no-cache
	docker-compose up -d

# View logs from load_balancer
logs:
	docker logs load_balancer

# View running containers
ps:
	docker ps

# Add new dynamic servers (example: Server4, Server5)
add:
	curl -X POST http://localhost:5050/add \
	  -H "Content-Type: application/json" \
	  -d '{"n": 2, "hostnames": ["Server4", "Server5"]}'

# Check active replicas via /rep
rep:
	curl http://localhost:5050/rep

# Remove dynamic servers (example: Server4, Server5)
rm:
	curl -X DELETE http://localhost:5050/rm \
	  -H "Content-Type: application/json" \
	  -d '{"n": 2, "hostnames": ["Server4", "Server5"]}'

# Test dynamic route to /home (request hashing)
route:
	curl http://localhost:5050/home

import docker
import random
import uuid
import string
import logging
import requests
from flask import Flask, request, jsonify
from consistent_hash import HashRing

app = Flask(__name__)
client = docker.from_env()
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

IMAGE_NAME = 'loadbalancingproject-server1'
NETWORK_NAME = 'loadbalancingproject_net1'

class LoadBalancer:
    def __init__(self):
        logger.info("==== Load Balancer Booted ====")
        self.hash_ring = HashRing(ring_size=2048, replicas=300)
        self.servers = {}  # hostname → node_key
        self.node_to_hostname = {}  # node_key → hostname

        for hostname in ["Server1", "Server2", "Server3"]:
            self._register_existing_server(hostname)

    def _register_existing_server(self, hostname):
        try:
            client.containers.get(hostname)
            node_key = hostname
            self.hash_ring.add_node(node_key)
            self.servers[hostname] = node_key
            self.node_to_hostname[node_key] = hostname
            logger.info(f"Registered container: {hostname}")
        except docker.errors.NotFound:
            logger.warning(f"Container {hostname} not found, skipping")

    def _spawn_server(self, hostname):
        if hostname in self.servers:
            logger.warning(f"{hostname} already exists, skipping")
            return False
        try:
            client.containers.run(
                image=IMAGE_NAME,
                name=hostname,
                network=NETWORK_NAME,
                environment={"SERVER_ID": hostname},
                detach=True
            )
            node_key = hostname
            self.hash_ring.add_node(node_key)
            self.servers[hostname] = node_key
            self.node_to_hostname[node_key] = hostname
            logger.info(f"Spawned and registered: {hostname}")
            return True
        except Exception as e:
            logger.error(f"Error spawning {hostname}: {e}")
            return False

    def _remove_server(self, hostname):
        if hostname not in self.servers:
            logger.warning(f"{hostname} not in registry")
            return False

        try:
            client.containers.get(hostname).remove(force=True)
        except docker.errors.NotFound:
            logger.warning(f"{hostname} not found during removal")

        node_key = self.servers[hostname]
        self.hash_ring.remove_node(node_key)
        del self.servers[hostname]
        del self.node_to_hostname[node_key]
        logger.info(f"Removed server: {hostname}")
        return True

lb = LoadBalancer()

@app.route('/rep', methods=['GET'])
def get_replicas():
    return jsonify({
        "message": {
            "N": len(lb.servers),
            "replicas": list(lb.servers.keys())
        },
        "status": "successful"
    }), 200

@app.route('/add', methods=['POST'])
def add_servers():
    data = request.get_json()
    logger.info("/add endpoint called")
    n = data.get('n', 0)
    hostnames = data.get('hostnames', [])

    if len(hostnames) > n:
        return jsonify({
            "message": "<Error> Too many hostnames provided",
            "status": "failure"
        }), 400

    for i in range(n):
        hostname = hostnames[i] if i < len(hostnames) else generate_hostname()
        lb._spawn_server(hostname)

    return jsonify({
        "message": {
            "N": len(lb.servers),
            "replicas": list(lb.servers.keys())
        },
        "status": "successful"
    }), 200

@app.route('/rm', methods=['DELETE'])
def remove_servers():
    data = request.get_json()
    n = data.get('n', 0)
    hostnames = data.get('hostnames', [])

    if len(hostnames) > n:
        return jsonify({
            "message": "<Error> Too many hostnames to remove",
            "status": "failure"
        }), 400

    removed = 0
    for h in hostnames:
        if removed < n and lb._remove_server(h):
            removed += 1

    remaining = list(lb.servers.keys())
    while removed < n and remaining:
        rand = random.choice(remaining)
        if lb._remove_server(rand):
            removed += 1
            remaining.remove(rand)

    return jsonify({
        "message": {
            "N": len(lb.servers),
            "replicas": list(lb.servers.keys())
        },
        "status": "successful"
    }), 200

@app.route('/<path:path>', methods=['GET'])
def route_request(path):
    if not lb.servers:
        return jsonify({
            "message": "<Error> No servers available",
            "status": "failure"
        }), 500

    request_id = int(uuid.uuid4()) % (2**32)
    node_key = lb.hash_ring.get_node_for_request(request_id)

    if node_key is None:
        return jsonify({
            "message": "<Error> No matching server",
            "status": "failure"
        }), 500

    hostname = lb.node_to_hostname[node_key]
    logger.info(f"[ROUTE] {request_id} → {hostname}")

    try:
        response = requests.get(f'http://{hostname}:5000/{path}', timeout=5)
        return response.json(), response.status_code
    except Exception as e:
        logger.error(f"[ERROR] Routing failed: {e}")
        return jsonify({
            "message": f"<Error> Failed to route to {hostname}: {e}",
            "status": "failure"
        }), 500

def generate_hostname():
    return ''.join(random.choices(string.ascii_lowercase + string.digits, k=8))

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
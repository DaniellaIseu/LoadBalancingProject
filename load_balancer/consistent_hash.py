import hashlib
import random

class HashRing:
    def __init__(self, ring_size=2048, replicas=300):
        self.ring_size = ring_size
        self.replicas = replicas
        self.ring = [None] * ring_size
        self.node_positions = {}
        self.num_nodes = 0

    def H(self, request_id):
        """Request hash function: Knuth-style"""
        return (request_id * 2654435761) % self.ring_size

    def Phi(self, node_key, replica_id):
        """Virtual node mapping using SHA256"""
        key = f"{node_key}-replica-{replica_id}".encode("utf-8")
        return int(hashlib.sha256(key).hexdigest(), 16) % self.ring_size

    def add_node(self, node_key):
        if node_key in self.node_positions:
            return False

        self.node_positions[node_key] = []
        for replica_id in range(self.replicas):
            slot = self.Phi(node_key, replica_id)
            original = slot
            while self.ring[slot] is not None:
                slot = (slot + 1) % self.ring_size
                if slot == original:
                    return False  # Ring full
            self.ring[slot] = node_key
            self.node_positions[node_key].append(slot)

        self.num_nodes += 1
        return True

    def remove_node(self, node_key):
        if node_key not in self.node_positions:
            return False

        for slot in self.node_positions[node_key]:
            self.ring[slot] = None

        del self.node_positions[node_key]
        self.num_nodes -= 1
        return True

    def get_node_for_request(self, request_id):
        if not self.node_positions:
            return None

        slot = self.H(request_id)
        for i in range(self.ring_size):
            probe = (slot + i) % self.ring_size
            if self.ring[probe] is not None:
                return self.ring[probe]
        return None

    def get_nodes(self):
        return list(self.node_positions.keys())
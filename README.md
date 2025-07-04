# Distributed Load Balancer with Consistent Hashing

This project implements a **lightweight distributed load balancer** using Flask and Docker. It routes incoming requests to backend servers using a **consistent hashing algorithm**, ensuring minimal disruption when servers are added or removed dynamically.

---

## Project Overview

The system is designed to:

- Simulate multiple backend servers (`Server1`, `Server2`, `Server3`, etc.)
- Use **consistent hashing** for intelligent request routing
- Dynamically **add/remove replicas** at runtime via API
- Be fully containerized with Docker
- Expose a simple HTTP API for testing and evaluation

---

## ⚙️ Architecture

<pre>
                 +---------------------+
                 |     Client (curl)   |
                 +----------+----------+
                            |
                            v
                 +---------------------+
                 |   Load Balancer     |  ← Flask app with Consistent HashRing
                 +----------+----------+
        ┌──────────────┬──────────────┬──────────────┐
        ↓              ↓              ↓              ↓
 +-----------+  +-----------+  +-----------+   +-------------+
 |  Server1  |  |  Server2  |  |  Server3  |   |  ...More...  |
 +-----------+  +-----------+  +-----------+   +-------------+
     Flask         Flask         Flask           Flask
</pre>
---

## Key Concepts

### Consistent Hashing
- Each request is assigned a 6-digit request ID.
- The load balancer hashes the request ID to locate the nearest virtual node.
- This ensures even distribution and minimal remapping during scaling.

### Dockerized Architecture
- All services (load balancer + servers) are containerized.
- Custom Dockerfiles used for both `load_balancer` and `server` images.
- Containers communicate using a user-defined Docker network (`load_balancer_net1`).

---

## API Endpoints

| Method | Endpoint           | Description                                      |
|--------|--------------------|--------------------------------------------------|
| GET    | `/rep`             | View current replica servers                    |
| POST   | `/add`             | Add one or more servers (supports hostname)     |
| DELETE | `/rm`              | Remove one or more servers                      |
| GET    | `/<path>`          | Proxy to backend (e.g., `/home` routes request) |

---

## Performance Analysis

We implemented an `analysis.py` script to evaluate:

- **Load distribution** across servers for 10,000 requests
- **Scalability** as new replicas are added incrementally
- **Request routing fairness** using simple counters

---

## Testing Highlights

- Confirmed that requests are distributed based on the hash ring, not round robin.
- Demonstrated minimal re-routing when adding/removing servers.
- Validated replica management with Docker container start/stop automation.
- Observed that earlier hash ring imbalance was resolved with `NODE_ID` consistency and correct image builds.

---

## Notes

- Flask is used only for demo purposes. In production, a WSGI server (e.g., Gunicorn) is preferred.
- The load balancer does not persist state — it's rebuilt each time.
- Server health checks or retries for failures are not implemented in this version.
- Default port for all servers is `5000`, bit if that does not work check `5050`.

---



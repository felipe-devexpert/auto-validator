import requests

from .base_plugin import BasePlugin


class DigitalOceanPlugin(BasePlugin):
    def __init__(self):
        self.required_fields = {
            "region": {"type": "choice", "values": ["nyc1", "nyc2", "nyc3", "sfo1", "sfo2", "sfo3", "sgp1", "lon1", "fra1", "tor1"]},
            "slug_type": {"type": "choice", "values": ["g-60vcpu-240gb-intel", "gd-60vcpu-240gb-intel", "c-60-intel", "c2-60vcpu-120gb-intel", "m-48vcpu-384gb-intel", "m3-48vcpu-384gb-intel", "so-48vcpu-384gb-intel"]},
            "image": {
                "type": "choice",
                "values": [
                    "ubuntu-20-04-x64",
                    "ubuntu-18-04-x64",
                ],
            },
            "ssh_keys": {"type": "number", "help_text": "ssh key id of digital ocean account"},
            "disk": {"type": "number", "min": 20, "max": 1024, "help_text": "in GB"},
            "name": {"type": "text", "min_length": 3, "max_length": 64, "help_text": "example.com"},
        }
    

    def create_machine(self, payload):
        url = "https://api.digitalocean.com/v2/droplets"
        API_KEY = payload.get("api_key")
        headers = {"Authorization": f"Bearer {API_KEY}"}
        data = {
            "region": payload.get("region"),
            "size": payload.get("slug_type"),
            "image": payload.get("image"),
            "ssh_keys": [payload.get("ssh_keys")],
            "name": payload.get("name"),
        }
        response = requests.post(url, headers=headers, json=data, timeout=30)
        if response.status_code == 200:
            data = response.json()
            response = {
                "id": data["id"],
                "region": data["region"]["slug"],
                "slug": data["size"]["slug"],
                "image": data["image"],
                "name": data["name"],
                "disk": data["size"]["disk"],
                "memory": data["size"]["memory"],
                "vcpus": data["size"]["vcpus"],
                "price": data["size"]["price_hourly"],
            }
            return response
        else:
            return None

    def destroy_machine(self, payload):
        droplet_id = payload.get("droplet_id")
        API_KEY = payload.get("api_key")
        url = f"https://api.digitalocean.com/v2/droplets/{droplet_id}"
        headers = {"Authorization": f"Bearer {API_KEY}"}
        response = requests.delete(url, headers=headers, timeout=30)
        return response.status_code == 200

    def list_available_machines(self):
        url = "https://api.digitalocean.com/v2/sizes"
        response = requests.get(url, timeout=30)
        list_of_machines = []
        if response.status_code == 200:
            for machine in response.json()["sizes"]:
                list_of_machines.append(
                    {
                        "slug": machine["slug"],
                        "memory": machine["memory"],
                        "vcpus": machine["vcpus"],
                        "disk": machine["disk"],
                        "transfer": machine["transfer"],
                        "price_monthly": machine["price_monthly"],
                        "price_hourly": machine["price_hourly"],
                    }
                )
            return list_of_machines
        else:
            return None

    def get_required_fields(self):
        return self.required_fields

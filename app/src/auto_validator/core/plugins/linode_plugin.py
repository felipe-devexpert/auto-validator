import requests

from .base_plugin import BasePlugin


class LinodePlugin(BasePlugin):
    def __init__(self):
        self.required_fields = {
            "region": {"type": "choice", "values": ["us-east", "us-west"]},
            "machine_type": {"type": "choice", "values": ["g6-nanode-1", "g6-standard-1"]},
            "image": {
                "type": "choice",
                "values": [
                    "linode/ubuntu20.04",
                ],
            },
            "root_password": {"type": "text", "min_length": 8, "max_length": 64, "help_text": "linenode@password"},
            "disk": {"type": "number", "min": 20, "max": 1024, "help_text": "in GB"},
            "label": {"type": "text", "min_length": 3, "max_length": 64, "help_text": "linode@label"},
        }

    def create_machine(self, payload):
        url = "https://api.linode.com/v4/linode/instances"
        API_KEY = payload.get("api_key")
        headers = {"Authorization": f"Bearer {API_KEY}"}
        data = {
            "region": payload.get("region"),
            "type": payload.get("machine_type"),
            "image": payload.get("image"),
            "root_pass": payload.get("root_password"),
            "label": payload.get("label"),
            "disk": payload.get("disk"),
        }
        response = requests.post(url, headers=headers, json=data, timeout=30)
        if response.status_code == 200:
            data = response.json()
            response = {
                "id": data["id"],
                "region": data["region"],
                "type": data["type"],
                "image": data["image"],
                "label": data["label"],
                "disk": data["specs"]["disk"],
                "memory": data["specs"]["memory"],
                "vcpus": data["specs"]["vcpus"],
                "price": data["specs"]["price"]["monthly"],
                "ip_address": data["ipv4"][0],
            }
            return response
        else:
            return None

    def destroy_machine(self, payload):
        INSTANCE_ID = payload.get("instance_id")
        API_KEY = payload.get("api_key")
        url = f"https://api.linode.com/v4/linode/instances/{INSTANCE_ID}"
        headers = {"Authorization": f"Bearer {API_KEY}"}
        response = requests.delete(url, headers=headers, timeout=30)
        return response.status_code == 200

    def list_available_machines(self):
        url = "https://api.linode.com/v4/linode/types"
        response = requests.get(url, timeout=30)
        list_of_machines = []
        if response.status_code == 200:
            for machine in response.json()["data"]:
                list_of_machines.append(
                    {
                        "id": machine["id"],
                        "label": machine["label"],
                        "disk": machine["disk"],
                        "memory": machine["memory"],
                        "vcpus": machine["vcpus"],
                        "price": machine["price"]["monthly"],
                    }
                )
            return list_of_machines
        else:
            return None

    def get_required_fields(self):
        return self.required_fields

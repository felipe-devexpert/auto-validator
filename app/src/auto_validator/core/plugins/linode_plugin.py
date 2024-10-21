import requests

from .base_plugin import BasePlugin


class LinodePlugin(BasePlugin):
    def __init__(self):
        self.required_fields = {
            "region": {"type": "choice", "values": []},
            "machine_type": {"type": "choice", "values": []},
            "image": {
                "type": "choice",
                "values": [
                    "linode/ubuntu20.04",
                ],
            },
            "root_password": {"type": "password", "min_length": 8, "max_length": 64, "help_text": "linenode@password"},
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
            return {"status": "success", "data": response}
        else:
            return {"status": "error", "data": response.json()}

    def destroy_machine(self, payload):
        INSTANCE_ID = payload.get("instance_id")
        API_KEY = payload.get("api_key")
        url = f"https://api.linode.com/v4/linode/instances/{INSTANCE_ID}"
        headers = {"Authorization": f"Bearer {API_KEY}"}
        response = requests.delete(url, headers=headers, timeout=30)
        if response.status_code == 200:
            return {"status": "success", "data": ""}
        else:
            return {"status": "error", "data": response.json()}

    def list_available_machines(self):
        url = "https://api.linode.com/v4/linode/types"
        response = requests.get(url, timeout=30)
        machines_list = []
        if response.status_code == 200:
            self.required_fields["machine_type"]["values"].clear()
            for machine in response.json()["data"]:
                machines_list.append(
                    {
                        "id": machine["id"],
                        "label": machine["label"],
                        "disk": machine["disk"],
                        "memory": machine["memory"],
                        "vcpus": machine["vcpus"],
                        "monthly price": machine["price"]["monthly"],
                        "hourly price": machine["price"]["hourly"],
                    }
                )
                self.required_fields["machine_type"]["values"].append(machine["id"])
            return {"status": "success", "data": machines_list}
        else:
            return {"status": "error", "data": response.json()}
    
    def list_available_regions(self):
        url = "https://api.linode.com/v4/regions"
        response = requests.get(url, timeout=30)
        regions_list = []
        if response.status_code == 200:
            self.required_fields["region"]["values"].clear()
            for region in response.json()["data"]:
                regions_list.append(
                    {
                        "id": region["id"],
                        "country": region["country"],
                        "label": region["label"],
                        "capabilities": region["capabilities"],
                    }
                )
                self.required_fields["region"]["values"].append(region["id"])
            return {"status": "success", "data": regions_list}
        else:
            return {"status": "error", "data": response.json()}

    def get_required_fields(self):
        self.list_available_regions()
        return self.required_fields

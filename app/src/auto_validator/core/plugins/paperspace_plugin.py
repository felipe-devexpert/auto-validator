import requests

from .base_plugin import BasePlugin


class PaperspacePlugin(BasePlugin):
    def __init__(self):
        self.required_fields = {
            "name": {"type": "text", "min_length": 3, "max_length": 64},
            "machine_type": {"type": "choice", "values": ["GPU+", "CPU+", "P4000", "P5000"]},
            "template_id": {"type": "choice", "values": ["tkni3aa4", "twnlo3zj"]},
            "disk_size": {"type": "number", "min": 20, "max": 1024},
            "region": {"type": "choice", "values": ["East Coast (NY2)", "West Coast (CA1)"]},
            "billing_type": {"type": "choice", "values": ["hourly", "monthly"]},
        }

    def create_machine(self, payload):
        url = "https://api.paperspace.com/v1/machines"
        API_KEY = payload.get("api_key")
        headers = {
            "Authorization": f"Bearer {API_KEY}",
        }
        data = {
            "name": payload.get("name"),
            "region": payload.get("region"),
            "machineType": payload.get("machine_type"),
            "diskSize": payload.get("disk_size"),
            "billingType": payload("billing_type"),
            "templateId": payload("template_id"),
        }
        response = requests.post(url, headers=headers, json=data, timeout=30)
        if response.status_code == 200:
            data = response.json()["data"]
            response = {
                "id": data["id"],
                "region": data["region"],
                "type": data["machineType"],
                "name": data["name"],
                "disk": data["storageTotal"],
                "ram": data["ram"],
                "cpus": data["cpus"],
            }
            return response
        else:
            return None

    def destroy_machine(self, payload):
        API_KEY = payload.get("api_key")
        machine_id = payload.get("machine_id")
        url = f"https://api.paperspace.com/v1/machines/{machine_id}"
        headers = {
            "Authorization": f"Bearer {API_KEY}",
        }
        response = requests.delete(url, headers=headers, timeout=30)
        return response.status_code == 200

    def list_available_machines(self, payload):
        url = "https://api.paperspace.com/v1/machines"
        API_KEY = payload.get("api_key")
        headers = {
            "Authorization": f"Bearer {API_KEY}",
        }
        response = requests.get(url, headers=headers, timeout=30)
        list_of_machines = []
        if response.status_code == 200:
            for machine in response.json()["items"]:
                list_of_machines.append(
                    {
                        "id": machine["id"],
                        "machine_type": machine["machineType"],
                        "name": machine["label"],
                        "disk": machine["disk"],
                        "ram": machine["ram"],
                        "cpus": machine["cpus"],
                        "price": machine["price"]["monthly"],
                    }
                )
            return list_of_machines
        else:
            return None

    def get_required_fields(self):
        return self.required_fields

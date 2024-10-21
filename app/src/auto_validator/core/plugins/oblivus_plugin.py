import requests

from .base_plugin import BasePlugin


class OblivusPlugin(BasePlugin):
    def __init__(self):
        self.required_fields = {
            "name": {"type": "text", "min_length": 3, "max_length": 64, "help_text": "VM name"},
            "flavor": {"type": "choice", "values": ["RTX_A6000_x8", "other_flavors"]},
            "location": {"type": "choice", "values": ["OSL1", "other_locations"]},
            "os": {"type": "choice", "values": ["UBUNTU", "other_os"]},
            "os_name": {"type": "choice", "values": ["ubuntu2204", "other_os_names"]},
            "authentication": {"type": "choice", "values": ["password", "ssh_key"]},
            "password": {"type": "text", "min_length": 8, "max_length": 64, "help_text": "Password for the VM"},
        }
    
    def get_machine_details(self, payload):
        API_KEY = payload.get("api_key")
        API_TOKEN = payload.get("api_token")
        VM_ID = payload.get("vm_id")
        url = f"https://api.oblivus.com/cloud/virtualserver/details/?apiKey={API_KEY}&apiToken={API_TOKEN}&vmID={VM_ID}"
        response = requests.get(url, timeout=30)
        if response.status_code == 200:
            return response.json()
        else:
            response.raise_for_status()

    def create_machine(self, payload):
        url = "https://api.oblivus.com/cloud/virtualserver/deploy/"
        data = {
            'apiKey': payload.get("api_key"),
            'apiToken': payload.get("api_token"),
            'name': payload.get("name"),
            'flavor': payload.get("flavor"),
            'location': payload.get("location"),
            'OS': payload.get("os"),
            'OSName': payload.get("os_name"),
            'authentication': payload.get("authentication"),
            'password': payload.get("password"),
        }
        response = requests.post(url, data=data, timeout=30)
        if response.status_code == 200:
            data = response.json()
            instance_id = data["instanceID"]
            response = self.get_machine_details({"api_key": payload.get("api_key"), "api_token": payload.get("api_token"), "vm_id": instance_id})
            if response.status_code == 200:
                data = response.json()
                response = {
                    "id": instance_id,
                    "name": data["name"],
                    "status": data["status"],
                    "location": data["location"],
                    "label": data["OS"]["label"],
                    "os_name": data["OS"]["name"],
                    "gpu": data["resources"]["GPU"],
                    "cpus": data["resources"]["vCPUValue"],
                    "ram": data["resources"]["ramValue"],
                    "disk": data["resources"]["systemDisk"]["size"],
                    "price": data["billing"]["hourlyCost"],
                    "ip_address": data["resources"]["IPAddress"],
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

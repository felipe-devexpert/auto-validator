import requests

from .base_plugin import BasePlugin

class RunPodPlugin(BasePlugin):
    def __init__(self):
        self.required_fields = {
            "gpuTypeId": {
            "type": "choice", 
            "values": [
                "NVIDIA RTX A6000", 
                "NVIDIA RTX A4000", 
                "NVIDIA RTX A4500", 
                "NVIDIA RTX A5000", 
                "AMD Instinct MI300X OAM", 
                "NVIDIA RTX 6000 Ada Generation"
            ]
            },
            "imageName": {
            "type": "choice", 
            "values": [
                "runpod/pytorch", 
                "runpod/tensorflow", 
                "runpod/jupyter"
            ]
            },
            "name": {
            "type": "text", 
            "min_length": 3, 
            "max_length": 64, 
            "help_text": "Machine name"
            },
            "ssh_keys": {
            "type": "list", 
            "help_text": "List of SSH key IDs to embed in the machine"
            },
        }
    def create_machine(self, payload):
        API_KEY = payload.get("api_key")
        url = "https://api.runpod.io/graphql?api_key={API_KEY}"
        headers = { "Content-Type": "application/json"}
        query = """
        mutation podRentInterruptable($input: PodRentInterruptableInput!){
            podRentInterruptable(input: $input) {
                id
                imageName
                env {
                    key
                    value
                }
                machineId
                machine {
                    podHostId
                    publicIp
                }
            }
        }
        """
        variables = {
            "input": {
                "bidPerGpu": 0.2,
                "cloudType": "SECURE",
                "gpuCount": 1,
                "volumeInGb": 40,
                "containerDiskInGb": 40,
                "minVcpuCount": 2,
                "minMemoryInGb": 15,
                "gpuTypeId": payload.get("gpuTypeId"),
                "name": payload.get("name"),
                "imageName": payload.get("imageName"),
                "dockerArgs": "",
                "ports": "8888/http",
                "volumeMountPath": "/workspace",
                "env": [
                    {"key": "JUPYTER_PASSWORD", "value": "vunw9ybnzqwpia2795p2"}
                ]
            }
        }
        response = requests.post(url, headers=headers, data={"query": query, "variables": variables}, timeout=30)
        if response.status_code == 200:
            data = response.json()
            machine_info = {
                "id": data["data"]["podRentInterruptable"]["id"],
                "name": data["data"]["podRentInterruptable"]["imageName"],
                "ip_address": data["data"]["podRentInterruptable"]["machine"]["podHostId"]
            }
            return machine_info
        else:
            response.raise_for_status()
    def destroy_machine(self, payload):
        API_KEY = payload.get("api_key")
        url = "https://api.runpod.io/graphql?api_key={API_KEY}"
        headers = { "Content-Type": "application/json"}
        query = """
        mutation podStop($input: PodStopInput!) {
            podStop(input: $input) {
                id
                desiredStatus
            }
        }
        """
        variables = {
            "input": {
                "podId": payload.get("id")
            }
        }
        response = requests.post(url, headers=headers, data={"query": query, "variables": variables}, timeout=30)
        if response.status_code == 200:
            return response.json()
        else:
            response.raise_for_status()
    def list_available_machines(self, payload):
        API_KEY = payload.get("api_key")
        url = "https://api.runpod.io/graphql?api_key={API_KEY}"
        headers = { "Content-Type": "application/json"}
        query = """
        query GpuTypes {
            gpuTypes {
                id
                displayName
                memoryInGb
            }
        }
        """
        response = requests.post(url, headers=headers, data={"query": query}, timeout=30)
        if response.status_code == 200:
            data = response.json()
            list_of_machines = []
            for machine in data["data"]["gpuTypes"]:
                list_of_machines.append(
                    {
                        "id": machine["id"],
                        "displayName": machine["displayName"],
                        "memoryInGb": machine["memoryInGb"],
                        "cudaCores": machine["cudaCores"],
                        "oneWeekPrice": machine["oneWeekPrice"]
                    }
                )
            return list_of_machines
        else:
            response.raise_for_status()
        return None
    
    def get_required_fields(self):
        return self.required_fields
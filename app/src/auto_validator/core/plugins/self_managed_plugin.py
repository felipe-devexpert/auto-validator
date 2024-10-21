from .base_plugin import BasePlugin


class SelfManagedPlugin(BasePlugin):
    def __init__(self):
        pass

    def create_machine(self, *args, **kwargs):
        return

    def destroy_machine(self, *args, **kwargs):
        return

    def list_available_machines(self, *args, **kwargs):
        return

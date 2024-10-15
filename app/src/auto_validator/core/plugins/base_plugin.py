class BasePlugin:
    def create_machine(self, payload):
        raise NotImplementedError("create_machine method is not implemented")

    def destroy_machine(self, payload):
        raise NotImplementedError("destroy_machine method is not implemented")

    def list_available_machines(self, payload):
        raise NotImplementedError("list_available_machines method is not implemented")

from .base_plugin import BasePlugin


class PluginManager:
    def __init__(self):
        self.plugins = {}

    def register_plugin(self, name, plugin):
        if not issubclass(plugin, BasePlugin):
            raise ValueError("Plugin must be a subclass of BasePlugin")
        self.plugins[name] = plugin()

    def get_plugin(self, name):
        return self.plugins.get(name)

    def get_registered_plugins(self):
        return self.plugins.keys()


plugin_manager = PluginManager()

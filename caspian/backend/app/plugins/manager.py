import importlib
import os

PLUGIN_FOLDER = os.path.dirname(__file__)


class PluginManager:
	def __init__(self):
		self.plugins = {}
		self.load_plugins()

	def load_plugins(self):
		for fname in os.listdir(PLUGIN_FOLDER):
			if fname.endswith(".py") and fname != "manager.py":
				mod_name = f"app.plugins.{fname[:-3]}"
				mod = importlib.import_module(mod_name)
				if hasattr(mod, "register"):
					self.plugins[fname[:-3]] = mod

	def call(self, plugin_name: str, *args, **kwargs):
		plugin = self.plugins.get(plugin_name)
		if not plugin:
			raise ValueError(f"Plugin '{plugin_name}' not found")
		return plugin.register(*args, **kwargs)


plugin_manager = PluginManager()

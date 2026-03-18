"""
Engine Core — Module Loader & Bootstrap

Loads modules, passes state and event bus, collects API functions.
"""

import importlib
import os
import sys
from typing import Any, Callable, Dict, List

from .state import GameState
from .events import EventBus


class ModuleLoader:
    """Loads and manages game modules."""

    def __init__(self, state: GameState, event_bus: EventBus):
        self.state = state
        self.event_bus = event_bus
        self.modules: Dict[str, Any] = {}
        self.api_functions: Dict[str, Callable] = {}

    def load_modules(self, modules_dir: str = None) -> None:
        """Scan and load all modules from the modules directory."""
        if modules_dir is None:
            modules_dir = os.path.join(os.path.dirname(__file__), "..", "modules")

        if not os.path.exists(modules_dir):
            print(f"Modules directory not found: {modules_dir}")
            return

        for filename in os.listdir(modules_dir):
            if filename.endswith("_module.py") and not filename.startswith("_"):
                module_name = filename[:-3]  # Remove .py
                self._load_module(module_name, modules_dir)

    def _load_module(self, module_name: str, modules_dir: str) -> None:
        """Load a single module."""
        try:
            # Add modules dir to path temporarily
            sys.path.insert(0, modules_dir)
            module = importlib.import_module(module_name)

            # Initialize module with state and event bus
            if hasattr(module, "init"):
                module.init(self.state, self.event_bus)

            # Collect API functions
            if hasattr(module, "get_api"):
                api = module.get_api()
                for func_name, func in api.items():
                    if func_name in self.api_functions:
                        print(f"Warning: API function '{func_name}' already registered")
                    self.api_functions[func_name] = func

            self.modules[module_name] = module
            print(f"✅ Loaded module: {module_name}")

        except Exception as e:
            print(f"❌ Failed to load module {module_name}: {e}")
        finally:
            if modules_dir in sys.path:
                sys.path.remove(modules_dir)

    def get_api(self) -> Dict[str, Callable]:
        """Get all registered API functions."""
        return self.api_functions

    def call_api(self, func_name: str, **kwargs) -> Any:
        """Call an API function by name."""
        if func_name not in self.api_functions:
            raise ValueError(f"Unknown API function: {func_name}")
        return self.api_functions[func_name](**kwargs)


class Engine:
    """Main engine that ties everything together."""

    def __init__(self):
        self.state = GameState()
        self.event_bus = EventBus()
        self.loader = ModuleLoader(self.state, self.event_bus)

    def start(self, modules_dir: str = None) -> None:
        """Start the engine and load all modules."""
        print("🎮 Starting VTT Engine...")
        self.loader.load_modules(modules_dir)
        print(f"📦 Loaded {len(self.loader.modules)} modules")
        print(f"🔧 Registered {len(self.loader.api_functions)} API functions")
        print("✅ Engine ready!")

    def get_state(self) -> Dict[str, Any]:
        """Get the current game state."""
        return self.state.to_dict()

    def get_api(self) -> Dict[str, Callable]:
        """Get all API functions."""
        return self.loader.get_api()

    def call_api(self, func_name: str, **kwargs) -> Any:
        """Call an API function."""
        return self.loader.call_api(func_name, **kwargs)

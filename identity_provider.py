import json
import os
import fcntl
import random
from typing import Dict, Tuple, List

REGISTRY_FILE = "clients_state.json"
LOCK_DIR = "./locks"

# Possible groups to assign randomly
ALL_GROUPS = ["finance", "hr", "dev", "sales", "it"]

class IdentityProvider:
    def __init__(self):
        self.lock_file = None
        self.client_id = None
        self.data = {}
        
        # Ensure directories exist
        os.makedirs(LOCK_DIR, exist_ok=True)
        if not os.path.exists(REGISTRY_FILE):
            with open(REGISTRY_FILE, "w") as f:
                json.dump({}, f)

    def acquire_identity(self) -> Dict:
        """Finds the first available client ID or creates a new one."""
        i = 1
        while True:
            candidate_id = f"client_{i}"
            lock_path = os.path.join(LOCK_DIR, f"{candidate_id}.lock")
            
            # 1. Try to open/create the lock file
            fp = open(lock_path, 'w')
            
            try:
                # 2. Try to acquire an exclusive lock (non-blocking)
                fcntl.lockf(fp, fcntl.LOCK_EX | fcntl.LOCK_NB)
                
                # SUCCESS: We successfully locked this ID. It is ours now.
                self.lock_file = fp
                self.client_id = candidate_id
                print(f"[Identity] Acquired Identity: {candidate_id}")
                
                # 3. Load or Init State
                return self._load_or_create_state(candidate_id)
                
            except IOError:
                # FAILURE: Someone else is running this client. Try next.
                fp.close()
                i += 1

    def _load_or_create_state(self, client_id: str) -> Dict:
        """Reads JSON registry to get persistent groups/segments."""
        with open(REGISTRY_FILE, "r") as f:
            full_registry = json.load(f)
        
        if client_id in full_registry:
            print(f"[Identity] Resuming previous state for {client_id}")
            self.data = full_registry[client_id]
        else:
            print(f"[Identity] Initializing NEW state for {client_id}")
            # Generate random groups
            groups = random.sample(ALL_GROUPS, 3)
            self.data = {
                "client_id": client_id,
                "tenant_id": "tenant-cp",
                "groups": groups,
                "assigned_segments": [] # Starts empty until policy arrives
            }
            self._save_state(full_registry)
            
        return self.data

    def update_segments(self, segments: List[str]):
        """Updates the local registry when a new policy arrives."""
        with open(REGISTRY_FILE, "r") as f:
            full_registry = json.load(f)
        
        if self.client_id in full_registry:
            full_registry[self.client_id]["assigned_segments"] = segments
            self.data["assigned_segments"] = segments
            self._save_state(full_registry)
            print("[Identity] Persisted new segments to disk.")

    def _save_state(self, registry):
        with open(REGISTRY_FILE, "w") as f:
            json.dump(registry, f, indent=4)

    def release(self):
        """Release the lock on exit."""
        if self.lock_file:
            self.lock_file.close() # OS releases lock automatically
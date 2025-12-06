import json
import os
import fcntl
import random
from typing import Dict, List

# Each agent gets its own file in this directory
STORAGE_DIR = "./agent_storage"
LOCK_DIR = "./locks"
ALL_GROUPS = ["finance", "hr", "dev", "sales", "it"]

class IdentityProvider:
    def __init__(self):
        self.lock_file = None
        self.client_id = None
        self.data = {}
        self.my_file_path = None
        
        # Ensure directories exist
        os.makedirs(LOCK_DIR, exist_ok=True)
        os.makedirs(STORAGE_DIR, exist_ok=True)

    def acquire_identity(self) -> Dict:
        """Finds the first available client ID by trying to lock files sequentially."""
        i = 1
        while True:
            candidate_id = f"client_{i}"
            lock_path = os.path.join(LOCK_DIR, f"{candidate_id}.lock")
            
            # Try to acquire an exclusive lock on this ID
            fp = open(lock_path, 'w')
            try:
                fcntl.lockf(fp, fcntl.LOCK_EX | fcntl.LOCK_NB)
                
                # Success - we own this ID now
                self.lock_file = fp
                self.client_id = candidate_id
                self.my_file_path = os.path.join(STORAGE_DIR, f"{candidate_id}.json")
                print(f"[Identity] Acquired Identity: {candidate_id}")
                return self._load_or_create_state()
                
            except IOError:
                # Locked by another process, try next ID
                fp.close()
                i += 1

    def _load_or_create_state(self) -> Dict:
        """Loads THIS agent's specific JSON file."""
        if os.path.exists(self.my_file_path):
            print(f"[Identity] Loading state from {self.my_file_path}")
            try:
                with open(self.my_file_path, "r") as f:
                    self.data = json.load(f)
            except json.JSONDecodeError:
                # Handle corrupted file
                print(f"[Identity] File corrupted, resetting state.")
                self._init_new_state()
        else:
            print(f"[Identity] No existing state. Initializing new.")
            self._init_new_state()
            
        return self.data

    def _init_new_state(self):
        self.data = {
            "client_id": self.client_id,
            "tenant_id": "tenant-cp",
            "groups": random.sample(ALL_GROUPS, 3),
            "assigned_segments": [] 
        }
        self._save_to_disk()

    def update_segments(self, segments: List[str]):
        """Updates the local state and writes to the specific agent file."""
        print(f"[Identity] Writing segments {segments} to {self.my_file_path}")
        self.data["assigned_segments"] = segments
        self._save_to_disk()

    def _save_to_disk(self):
        """Atomic write to the specific agent file."""
        temp_file = self.my_file_path + ".tmp"
        with open(temp_file, "w") as f:
            json.dump(self.data, f, indent=4)
            f.flush()
            os.fsync(f.fileno()) # Force write to physical disk
        
        os.replace(temp_file, self.my_file_path)
        print(f"[Identity] 💾 Saved.")

    def release(self):
        if self.lock_file:
            self.lock_file.close()
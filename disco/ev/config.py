from __future__ import annotations
from pathlib import Path
from typing import Optional, Union



class Feeder:
    def __init__(self, master_file, name=None):
        self.master_file = Path(master_file)
        self.name = name or self.master_file.parent.name
    
    @classmethod
    def from_opendss(cls, master_file) -> Feeder:
        return cls(master_file)

    def validate(self) -> bool:
        if not self.master_file.exists():
            raise FileNotFoundError(f"Master file not found: {self.master_file}")
        return True

    def __repr__(self) -> str:
        return f"Feeder(name={self.name!r}, master_file={str(self.master_file)!r})"
from dataclasses import dataclass
from typing import List, Optional

@dataclass
class NodeHistory:
    timestamps: List[str]
    cpu_load: List[float]
    occupied_memory: List[float]
    total_memory: List[float]
    epoch: int
    epoch_avail: float
    uptime: str
    version: str
    cpu_temp: Optional[List[float]] = None
    gpu_load: Optional[List[float]] = None
    gpu_occupied_memory: Optional[List[float]] = None
    gpu_total_memory: Optional[List[float]] = None
    gpu_temp: Optional[List[float]] = None

    @classmethod
    def from_dict(cls, data: dict) -> 'NodeMetrics':
        # Clean up GPU-related lists - if all values are None, set the whole list to None
        gpu_fields = ['gpu_load', 'gpu_occupied_memory', 'gpu_total_memory', 'gpu_temp']
        for field in gpu_fields:
            if field in data and all(v is None for v in data[field]):
                data[field] = None

        return cls(
            timestamps=data['timestamps'],
            cpu_load=data['cpu_load'],
            occupied_memory=data['occupied_memory'],
            total_memory=data['total_memory'],
            epoch=data['epoch'],
            epoch_avail=data['epoch_avail'],
            uptime=data['uptime'],
            version=data['version'],
            cpu_temp=data.get('cpu_temp'),
            gpu_load=data.get('gpu_load'),
            gpu_occupied_memory=data.get('gpu_occupied_memory'),
            gpu_total_memory=data.get('gpu_total_memory'),
            gpu_temp=data.get('gpu_temp')
        )
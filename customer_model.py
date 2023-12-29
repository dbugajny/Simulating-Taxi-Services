from enum import Enum
from typing import Optional


class CustomerStatus(Enum):
    NO_TAXI = 1
    WAITING = 2
    INSIDE = 3
    END = 4


class Customer:
    def __init__(self, current_vertex: str, destination_vertex: str):
        self.status: CustomerStatus = CustomerStatus.NO_TAXI
        self.assigned_taxi: Optional[str] = None
        self.current_vertex: str = current_vertex
        self.destination_vertex: str = destination_vertex
        self.pickup_path: Optional[list[str]] = None
        self.destination_path: Optional[list[str]] = None
        self.waiting_time = 0

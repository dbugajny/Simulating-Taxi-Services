import random

import numpy as np

from customer_model import Customer, CustomerStatus
from taxi_model import Taxi, TaxiStatus

INITIAL_FEE = 5
LENGTH_FEE = 2
N_TAXIS = 3
TIME_RATE = 15  # in seconds
MAX_TAXI_WORKING_TIME = 8 * 60 * 24

CUSTOMERS_TO_TAXIS_RATIO = 1

CUSTOMER_PROBA_LST = [
    0.09, 0.05, 0.02, 0.01, 0.01, 0.01, 0.03, 0.09, 0.14, 0.14,
    0.13, 0.14, 0.16, 0.16, 0.17, 0.16, 0.13, 0.18, 0.25, 0.25,
    0.22, 0.22, 0.2, 0.15
]


class TaxiService:
    def __init__(self, city_plan):
        self.customers: list[Customer] = []
        self.city_plan: dict[str, list[str]] = city_plan
        self.taxis: dict[str, Taxi] = {}
        self.n_active_taxis = 0
        self.taxis_in_vertices = {k: [] for k in city_plan.keys()}
        self.new_taxi_key: int = 1
        self.time = [0, 0, 0]

    def assign_taxis_to_customers(self):
        for customer in self.customers:
            if customer.status != CustomerStatus.NO_TAXI:
                continue
            taxi_id, pickup_path = self.find_closest_taxi(customer.current_vertex)
            if taxi_id:
                customer.assigned_taxi = taxi_id
                customer.pickup_path = pickup_path
                customer.status = CustomerStatus.WAITING

                self.taxis[taxi_id].status = TaxiStatus.GOING_TO_CUSTOMER
                self.taxis[taxi_id].n_customers_delivered += 1
                self.taxis[taxi_id].total_income += INITIAL_FEE
            else:
                customer.waiting_time += 15

    @staticmethod
    def _create_path(current_vertex, predecessors):
        path = []
        vertex = predecessors[current_vertex]

        while vertex:
            path.append(vertex)
            vertex = predecessors[vertex]

        return path

    def find_closest_taxi(self, customer_vertex):
        predecessors = {customer_vertex: None}
        visited = {customer_vertex}
        queue = [customer_vertex]

        while queue:
            processed_vertex = queue.pop(0)
            for taxi in self.taxis_in_vertices[processed_vertex]:
                if self.taxis[taxi].status == TaxiStatus.FREE:
                    path = self._create_path(processed_vertex, predecessors)
                    return taxi, path

            for neighbour_vertex in self.city_plan[processed_vertex]:
                if neighbour_vertex not in visited:
                    visited.add(neighbour_vertex)
                    queue.append(neighbour_vertex)
                    predecessors[neighbour_vertex] = processed_vertex
        return None, None

    def find_destination_path(self, customer_vertex, destination_vertex):
        predecessors = {destination_vertex: None}
        visited = {destination_vertex}
        queue = [destination_vertex]

        while queue:
            processed_vertex = queue.pop(0)
            if processed_vertex == customer_vertex:
                path = self._create_path(processed_vertex, predecessors)
                return path

            for neighbour_vertex in self.city_plan[processed_vertex]:
                if neighbour_vertex not in visited:
                    visited.add(neighbour_vertex)
                    queue.append(neighbour_vertex)
                    predecessors[neighbour_vertex] = processed_vertex

        return None

    def generate_new_taxi(self):
        if len(self.customers) / max(self.n_active_taxis, 1) < CUSTOMERS_TO_TAXIS_RATIO:
            return

        possible_lst = list(self.city_plan.keys())
        current_vertex = np.random.choice(possible_lst)

        new_key = str(self.new_taxi_key)
        self.new_taxi_key += 1

        self.taxis[new_key] = Taxi(current_vertex)
        self.taxis_in_vertices[current_vertex].append(new_key)
        self.n_active_taxis += 1

    def _generate_new_customer(self):
        possible_lst = list(self.city_plan.keys())
        current_vertex = np.random.choice(possible_lst)
        possible_lst.remove(current_vertex)
        destination_vertex = np.random.choice(possible_lst)

        customer = Customer(current_vertex, destination_vertex)
        customer.destination_path = self.find_destination_path(current_vertex, destination_vertex)

        self.customers.append(customer)

    def generate_new_customers(self):
        # customer_proba = [0.99, 0.005, 0.005]
        if random.uniform(0, 1) < CUSTOMER_PROBA_LST[self.time[0]]:
            self._generate_new_customer()

    def _process_customer_waiting(self, customer):
        if customer.pickup_path:
            customer.waiting_time += 15

            current_vertex = self.taxis[customer.assigned_taxi].current_vertex
            new_vertex = customer.pickup_path.pop(0)

            self.taxis_in_vertices[current_vertex].remove(customer.assigned_taxi)
            self.taxis_in_vertices[new_vertex].append(customer.assigned_taxi)

            self.taxis[customer.assigned_taxi].current_vertex = new_vertex
            self.taxis[customer.assigned_taxi].total_distance += 1

        else:
            customer.status = CustomerStatus.INSIDE

    def _process_customer_inside(self, customer):
        if customer.destination_path:
            current_vertex = self.taxis[customer.assigned_taxi].current_vertex
            new_vertex = customer.destination_path.pop(0)

            self.taxis_in_vertices[current_vertex].remove(customer.assigned_taxi)
            self.taxis_in_vertices[new_vertex].append(customer.assigned_taxi)

            customer.current_vertex = new_vertex
            self.taxis[customer.assigned_taxi].current_vertex = new_vertex
            self.taxis[customer.assigned_taxi].total_distance += 1
            self.taxis[customer.assigned_taxi].total_income += LENGTH_FEE

        else:
            customer.status = CustomerStatus.END

    def process_taxis(self):
        taxis_to_del = []
        for key, taxi in self.taxis.values():
            taxi.working_time += TIME_RATE

            if taxi.status == TaxiStatus.FREE and taxi.working_time >= MAX_TAXI_WORKING_TIME:
                taxis_to_del.append(key)

        for taxi_to_del in taxis_to_del:
            del self.taxis[taxi_to_del]

    def make_step(self):
        self.generate_new_customers()
        self.generate_new_taxi()
        self.assign_taxis_to_customers()

        customers_to_delete = []

        for i, customer in enumerate(self.customers):
            if customer.status == CustomerStatus.WAITING:
                self._process_customer_waiting(customer)
            elif customer.status == CustomerStatus.INSIDE:
                self._process_customer_inside(customer)
            elif customer.status == CustomerStatus.END:
                self.taxis[customer.assigned_taxi].status = TaxiStatus.FREE
                customers_to_delete.append(i)

        for i in customers_to_delete[::-1]:
            del self.customers[i]

        self.update_time()
        self.process_taxis()

    def update_time(self):
        self.time[2] += TIME_RATE

        if self.time[2] == 60:
            self.time[2] = 0
            self.time[1] += 1

            if self.time[1] == 60:
                self.time[1] = 0
                self.time[0] += 1

                if self.time[0] == 24:
                    self.time[0] = 0

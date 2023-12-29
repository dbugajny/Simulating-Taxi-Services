import random

import numpy as np

from customer_model import Customer, CustomerStatus
from taxi_model import Taxi, TaxiStatus

INITIAL_FEE = 5
LENGTH_FEE = 2
N_TAXIS = 3

CUSTOMER_PROBA_LST = [
    0.35, 0.18, 0.10, 0.05, 0.03, 0.03,
    0.13, 0.38, 0.55, 0.56, 0.52, 0.57,
    0.63, 0.62, 0.67, 0.63, 0.50, 0.71,
    1.00, 0.99, 0.86, 0.86, 0.79, 0.59
]


class TaxiService:
    def __init__(self, city_plan):
        self.customers: list[Customer] = []
        self.city_plan: dict[str, list[str]] = city_plan
        self.taxis: dict[str, Taxi] = {}
        self.taxis_in_vertices = {k: [] for k in city_plan.keys()}
        self.new_taxi_key: int = 1
        self.time = [0, 0]

        for i in range(N_TAXIS):
            self.generate_new_taxi()

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
                customer.waiting_time += 1

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
        possible_lst = list(self.city_plan.keys())
        current_vertex = np.random.choice(possible_lst)

        new_key = str(self.new_taxi_key)
        self.new_taxi_key += 1

        self.taxis[new_key] = Taxi(current_vertex)
        self.taxis_in_vertices[current_vertex].append(new_key)

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
            customer.waiting_time += 1

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

    def make_step(self):
        self.generate_new_customers()
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

    def update_time(self):
        self.time[1] += 1

        if self.time[1] == 60:
            self.time[1] = 0
            self.time[0] += 1

            if self.time[0] == 24:
                self.time[0] = 0
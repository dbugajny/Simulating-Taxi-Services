import numpy as np

from customer_model import Customer, CustomerStatus
from taxi_model import Taxi, TaxiStatus

INITIAL_FEE = 5
LENGTH_FEE = 2


class TaxiService:
    def __init__(self, graph):
        self.customers: list[Customer] = []
        self.graph = graph

        self.taxis: dict[str, Taxi] = {}
        self.taxis_in_vertices = {k: [] for k in graph.keys()}
        self.customers_in_vertices = {k: [] for k in graph.keys()}
        self.new_taxi_key: int = 1

        for i in range(3):
            self.generate_new_taxi()

        for i in range(5):
            self._generate_new_customer()

    def assign_taxi_to_customer(self):
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
                return

    @staticmethod
    def _create_path(cur_ver, predecessors):
        path = []

        res = predecessors[cur_ver]

        while res:
            path.append(res)
            res = predecessors[res]

        return path

    def find_closest_taxi(self, customer_vertex):
        predecessors = {customer_vertex: None}
        visited = {customer_vertex}
        queue = [customer_vertex]
        while queue:
            cur_ver = queue.pop(0)
            for taxi in self.taxis_in_vertices[cur_ver]:
                if self.taxis[taxi].status == TaxiStatus.FREE:
                    path = self._create_path(cur_ver, predecessors)

                    return taxi, path
            for ver_edg in self.graph[cur_ver]:
                if ver_edg not in visited:
                    visited.add(ver_edg)
                    queue.append(ver_edg)
                    predecessors[ver_edg] = cur_ver
        return None, None

    def find_destination_path(self, customer_vertex, destination_vertex):
        predecessors = {destination_vertex: None}
        visited = {destination_vertex}
        queue = [destination_vertex]
        while queue:
            cur_ver = queue.pop(0)
            if cur_ver == customer_vertex:
                path = self._create_path(cur_ver, predecessors)

                return path

            for ver_edg in self.graph[cur_ver]:
                if ver_edg not in visited:
                    visited.add(ver_edg)
                    queue.append(ver_edg)
                    predecessors[ver_edg] = cur_ver

        return None

    def generate_new_taxi(self):
        possible_lst = list(self.graph.keys())
        current_vertex = np.random.choice(possible_lst)

        new_key = str(self.new_taxi_key)
        self.new_taxi_key += 1

        self.taxis[new_key] = Taxi(current_vertex)
        self.taxis_in_vertices[current_vertex].append(new_key)

    def _generate_new_customer(self):
        possible_lst = list(self.graph.keys())
        current_vertex = np.random.choice(possible_lst)
        possible_lst.remove(current_vertex)
        destination_vertex = np.random.choice(possible_lst)

        customer = Customer(current_vertex, destination_vertex)
        customer.destination_path = self.find_destination_path(current_vertex, destination_vertex)

        self.customers.append(customer)

    def generate_new_customers(self):
        customer_proba = [0.99, 0.005, 0.005]
        n_new_customers = np.random.choice(list(range(len(customer_proba))), p=customer_proba)

        for _ in range(n_new_customers):
            self._generate_new_customer()

    def _process_customer_waiting(self, customer):
        if customer.pickup_path:
            new_ver = customer.pickup_path.pop(0)
            self.taxis[customer.assigned_taxi].current_vertex = new_ver
            self.taxis[customer.assigned_taxi].total_distance += 1
        else:
            customer.status = CustomerStatus.INSIDE

    def _process_customer_inside(self, customer):
        if customer.destination_path:
            new_ver = customer.destination_path.pop(0)
            customer.current_vertex = new_ver
            self.taxis[customer.assigned_taxi].current_vertex = new_ver
            self.taxis[customer.assigned_taxi].total_distance += 1
            self.taxis[customer.assigned_taxi].total_income += LENGTH_FEE
        else:
            customer.status = CustomerStatus.END

    def make_step(self):
        self.generate_new_customers()
        self.assign_taxi_to_customer()

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

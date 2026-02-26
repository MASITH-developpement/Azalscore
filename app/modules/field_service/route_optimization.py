"""
AZALS MODULE 17 - Route Optimization Service (GAP-002)
========================================================
Service d'optimisation des tournées avec algorithmes TSP/VRP.

Algorithmes implémentés:
- Nearest Neighbor (rapide, solution initiale)
- 2-opt (amélioration locale)
- Or-opt (amélioration locale)
- Simulated Annealing (métaheuristique globale)
- Savings Algorithm (Clarke-Wright)
- Time Window optimization

Fonctionnalités:
- Optimisation mono-véhicule (TSP)
- Optimisation multi-véhicules (VRP)
- Respect des fenêtres horaires
- Prise en compte des temps de trajet
- Contraintes de capacité véhicule
- Équilibrage de charge entre techniciens
"""
from __future__ import annotations


import math
import random
import uuid
from dataclasses import dataclass, field
from datetime import date, time, datetime, timedelta
from decimal import Decimal
from enum import Enum
from typing import Callable

from sqlalchemy.orm import Session

from .models import (
    Route,
    Intervention,
    Technician,
    Vehicle,
    InterventionStatus,
)


# ============================================================================
# CONSTANTS
# ============================================================================

# Vitesse moyenne de déplacement en km/h (milieu urbain/périurbain)
AVERAGE_SPEED_KMH = 40

# Temps de service par défaut si non spécifié (minutes)
DEFAULT_SERVICE_TIME = 60

# Rayon de la Terre en km (pour formule Haversine)
EARTH_RADIUS_KM = 6371

# Température initiale pour Simulated Annealing
SA_INITIAL_TEMP = 10000

# Taux de refroidissement
SA_COOLING_RATE = 0.9995

# Itérations minimales sans amélioration avant arrêt
SA_MIN_ITERATIONS = 1000

# Nombre max d'itérations 2-opt
OPT2_MAX_ITERATIONS = 5000


# ============================================================================
# DATA CLASSES
# ============================================================================

@dataclass
class Location:
    """Représente un point géographique."""
    id: str
    name: str
    lat: float
    lng: float

    # Contraintes temporelles
    time_window_start: time | None = None
    time_window_end: time | None = None

    # Durée de service (minutes)
    service_time: int = DEFAULT_SERVICE_TIME

    # Priorité (1=plus haute)
    priority: int = 3

    # Charge (poids, volume)
    weight: float = 0
    volume: float = 0

    # Compétences requises
    required_skills: list[str] = field(default_factory=list)


@dataclass
class VehicleConstraints:
    """Contraintes du véhicule."""
    max_weight: float = float('inf')
    max_volume: float = float('inf')
    max_distance_km: float = float('inf')
    max_duration_minutes: int = 480  # 8 heures

    # Heures de travail
    work_start: time = time(8, 0)
    work_end: time = time(18, 0)

    # Pause obligatoire
    break_duration: int = 60
    break_window_start: time = time(12, 0)
    break_window_end: time = time(14, 0)


@dataclass
class RouteStop:
    """Un arrêt dans la tournée."""
    location: Location
    arrival_time: time | None = None
    departure_time: time | None = None
    waiting_time: int = 0  # Minutes d'attente
    travel_time_from_prev: int = 0  # Minutes depuis arrêt précédent
    distance_from_prev: float = 0  # km depuis arrêt précédent


@dataclass
class OptimizedRoute:
    """Résultat d'optimisation d'une tournée."""
    stops: list[RouteStop]
    total_distance: float  # km
    total_duration: int  # minutes (trajet + service)
    total_service_time: int  # minutes
    total_travel_time: int  # minutes
    total_waiting_time: int  # minutes
    optimization_score: float  # 0-100
    algorithm_used: str
    computation_time_ms: int
    feasible: bool = True
    violations: list[str] = field(default_factory=list)


@dataclass
class VRPSolution:
    """Solution VRP multi-véhicules."""
    routes: dict[str, OptimizedRoute]  # technician_id -> route
    total_distance: float
    total_duration: int
    unassigned_locations: list[Location]
    balance_score: float  # Équilibre entre véhicules (0-100)
    overall_score: float
    computation_time_ms: int


class OptimizationAlgorithm(str, Enum):
    """Algorithmes d'optimisation disponibles."""
    NEAREST_NEIGHBOR = "nearest_neighbor"
    TWO_OPT = "2-opt"
    OR_OPT = "or-opt"
    SIMULATED_ANNEALING = "simulated_annealing"
    SAVINGS = "savings"
    HYBRID = "hybrid"  # Nearest neighbor + 2-opt + Or-opt


# ============================================================================
# DISTANCE & TIME CALCULATIONS
# ============================================================================

def haversine_distance(lat1: float, lng1: float, lat2: float, lng2: float) -> float:
    """
    Calcule la distance entre deux points en km (formule de Haversine).

    Plus précis que la distance euclidienne pour les coordonnées GPS.
    """
    lat1_rad = math.radians(lat1)
    lat2_rad = math.radians(lat2)
    delta_lat = math.radians(lat2 - lat1)
    delta_lng = math.radians(lng2 - lng1)

    a = (math.sin(delta_lat / 2) ** 2 +
         math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(delta_lng / 2) ** 2)
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

    return EARTH_RADIUS_KM * c


def calculate_travel_time(distance_km: float, speed_kmh: float = AVERAGE_SPEED_KMH) -> int:
    """Calcule le temps de trajet en minutes."""
    if speed_kmh <= 0:
        return 0
    return int((distance_km / speed_kmh) * 60)


def build_distance_matrix(locations: list[Location]) -> list[list[float]]:
    """Construit la matrice des distances entre toutes les locations."""
    n = len(locations)
    matrix = [[0.0] * n for _ in range(n)]

    for i in range(n):
        for j in range(i + 1, n):
            dist = haversine_distance(
                locations[i].lat, locations[i].lng,
                locations[j].lat, locations[j].lng
            )
            matrix[i][j] = dist
            matrix[j][i] = dist

    return matrix


def time_to_minutes(t: time) -> int:
    """Convertit une heure en minutes depuis minuit."""
    return t.hour * 60 + t.minute


def minutes_to_time(minutes: int) -> time:
    """Convertit des minutes depuis minuit en heure."""
    hours = (minutes // 60) % 24
    mins = minutes % 60
    return time(hours, mins)


# ============================================================================
# TSP ALGORITHMS
# ============================================================================

class TSPSolver:
    """Solveur TSP (Traveling Salesman Problem)."""

    def __init__(
        self,
        locations: list[Location],
        depot: Location | None = None,
        constraints: VehicleConstraints | None = None
    ):
        self.locations = locations
        self.depot = depot
        self.constraints = constraints or VehicleConstraints()
        self.n = len(locations)

        # Ajoute le dépôt au début si présent
        if depot:
            self.all_locations = [depot] + locations + [depot]  # Retour au dépôt
        else:
            self.all_locations = locations

        self.distance_matrix = build_distance_matrix(self.all_locations)

    def nearest_neighbor(self) -> list[int]:
        """
        Algorithme du plus proche voisin.

        Complexité: O(n²)
        Qualité: Solution initiale acceptable (~20-25% au-dessus de l'optimal)
        """
        if not self.locations:
            return []

        n = len(self.all_locations)
        visited = [False] * n
        tour = [0]  # Commence au dépôt (ou première location)
        visited[0] = True

        current = 0
        for _ in range(n - 1):
            nearest = -1
            min_dist = float('inf')

            for j in range(n):
                if not visited[j] and self.distance_matrix[current][j] < min_dist:
                    # Vérifie les contraintes de fenêtre horaire
                    if self._can_visit(tour, j):
                        min_dist = self.distance_matrix[current][j]
                        nearest = j

            if nearest == -1:
                # Aucun voisin valide trouvé (contraintes)
                break

            visited[nearest] = True
            tour.append(nearest)
            current = nearest

        return tour

    def two_opt(self, tour: list[int], max_iterations: int = OPT2_MAX_ITERATIONS) -> list[int]:
        """
        Amélioration 2-opt.

        Inverse des segments de la tournée pour réduire la distance totale.
        Complexité: O(n² × iterations)
        """
        if len(tour) < 4:
            return tour

        improved = True
        best_tour = tour.copy()
        best_distance = self._calculate_tour_distance(best_tour)
        iteration = 0

        while improved and iteration < max_iterations:
            improved = False
            iteration += 1

            for i in range(1, len(best_tour) - 2):
                for j in range(i + 1, len(best_tour) - 1):
                    # Inverse le segment entre i et j
                    new_tour = (
                        best_tour[:i] +
                        best_tour[i:j+1][::-1] +
                        best_tour[j+1:]
                    )

                    new_distance = self._calculate_tour_distance(new_tour)

                    if new_distance < best_distance:
                        if self._is_feasible(new_tour):
                            best_tour = new_tour
                            best_distance = new_distance
                            improved = True

        return best_tour

    def or_opt(self, tour: list[int]) -> list[int]:
        """
        Amélioration Or-opt.

        Déplace des segments de 1, 2 ou 3 clients vers d'autres positions.
        """
        if len(tour) < 4:
            return tour

        improved = True
        best_tour = tour.copy()
        best_distance = self._calculate_tour_distance(best_tour)

        while improved:
            improved = False

            for segment_size in [1, 2, 3]:
                for i in range(1, len(best_tour) - segment_size):
                    segment = best_tour[i:i + segment_size]
                    remaining = best_tour[:i] + best_tour[i + segment_size:]

                    for j in range(1, len(remaining)):
                        new_tour = remaining[:j] + segment + remaining[j:]
                        new_distance = self._calculate_tour_distance(new_tour)

                        if new_distance < best_distance - 0.001:
                            if self._is_feasible(new_tour):
                                best_tour = new_tour
                                best_distance = new_distance
                                improved = True
                                break

                    if improved:
                        break

                if improved:
                    break

        return best_tour

    def simulated_annealing(
        self,
        initial_tour: list[int],
        initial_temp: float = SA_INITIAL_TEMP,
        cooling_rate: float = SA_COOLING_RATE,
        min_iterations: int = SA_MIN_ITERATIONS
    ) -> list[int]:
        """
        Métaheuristique Simulated Annealing.

        Explore l'espace des solutions en acceptant parfois des solutions
        moins bonnes pour échapper aux optima locaux.
        """
        if len(initial_tour) < 4:
            return initial_tour

        current_tour = initial_tour.copy()
        current_distance = self._calculate_tour_distance(current_tour)

        best_tour = current_tour.copy()
        best_distance = current_distance

        temperature = initial_temp
        iterations_without_improvement = 0

        while temperature > 1 and iterations_without_improvement < min_iterations:
            # Génère une solution voisine (swap ou 2-opt)
            new_tour = self._generate_neighbor(current_tour)
            new_distance = self._calculate_tour_distance(new_tour)

            delta = new_distance - current_distance

            # Accepte si meilleur ou selon probabilité de Boltzmann
            if delta < 0 or random.random() < math.exp(-delta / temperature):
                if self._is_feasible(new_tour):
                    current_tour = new_tour
                    current_distance = new_distance

                    if current_distance < best_distance:
                        best_tour = current_tour.copy()
                        best_distance = current_distance
                        iterations_without_improvement = 0
                    else:
                        iterations_without_improvement += 1
                else:
                    iterations_without_improvement += 1
            else:
                iterations_without_improvement += 1

            temperature *= cooling_rate

        return best_tour

    def _generate_neighbor(self, tour: list[int]) -> list[int]:
        """Génère une solution voisine par swap ou inversion."""
        if len(tour) < 4:
            return tour

        new_tour = tour.copy()

        if random.random() < 0.5:
            # Swap deux positions (pas le dépôt)
            i = random.randint(1, len(tour) - 2)
            j = random.randint(1, len(tour) - 2)
            if i != j:
                new_tour[i], new_tour[j] = new_tour[j], new_tour[i]
        else:
            # Inversion d'un segment (2-opt move)
            i = random.randint(1, len(tour) - 3)
            j = random.randint(i + 1, len(tour) - 2)
            new_tour = tour[:i] + tour[i:j+1][::-1] + tour[j+1:]

        return new_tour

    def _calculate_tour_distance(self, tour: list[int]) -> float:
        """Calcule la distance totale d'une tournée."""
        if len(tour) < 2:
            return 0

        total = 0
        for i in range(len(tour) - 1):
            total += self.distance_matrix[tour[i]][tour[i + 1]]

        return total

    def _can_visit(self, current_tour: list[int], next_idx: int) -> bool:
        """Vérifie si on peut visiter la prochaine location (fenêtre horaire)."""
        loc = self.all_locations[next_idx]

        if loc.time_window_start is None or loc.time_window_end is None:
            return True

        # Calcule l'heure d'arrivée estimée
        if not current_tour:
            arrival_minutes = time_to_minutes(self.constraints.work_start)
        else:
            # Temps de trajet depuis la dernière position
            last_idx = current_tour[-1]
            dist = self.distance_matrix[last_idx][next_idx]
            travel_time = calculate_travel_time(dist)

            # Heure de départ de la position précédente
            prev_loc = self.all_locations[last_idx]
            departure = time_to_minutes(self.constraints.work_start) + prev_loc.service_time

            for idx in current_tour[1:]:
                stop_loc = self.all_locations[idx]
                departure += stop_loc.service_time + calculate_travel_time(
                    self.distance_matrix[current_tour[current_tour.index(idx) - 1]][idx]
                )

            arrival_minutes = departure + travel_time

        window_end = time_to_minutes(loc.time_window_end)

        return arrival_minutes <= window_end

    def _is_feasible(self, tour: list[int]) -> bool:
        """Vérifie si une tournée respecte toutes les contraintes."""
        if len(tour) < 2:
            return True

        total_distance = self._calculate_tour_distance(tour)
        if total_distance > self.constraints.max_distance_km:
            return False

        total_travel_time = calculate_travel_time(total_distance)
        total_service_time = sum(
            self.all_locations[idx].service_time
            for idx in tour[1:-1]  # Exclut dépôts
        )

        total_duration = total_travel_time + total_service_time
        if total_duration > self.constraints.max_duration_minutes:
            return False

        # Vérification des fenêtres horaires
        current_time = time_to_minutes(self.constraints.work_start)

        for i, idx in enumerate(tour[1:-1], 1):
            loc = self.all_locations[idx]
            travel_time = calculate_travel_time(self.distance_matrix[tour[i-1]][idx])
            current_time += travel_time

            if loc.time_window_start and loc.time_window_end:
                window_start = time_to_minutes(loc.time_window_start)
                window_end = time_to_minutes(loc.time_window_end)

                if current_time < window_start:
                    current_time = window_start  # Attente
                elif current_time > window_end:
                    return False  # Trop tard

            current_time += loc.service_time

        return True

    def solve(
        self,
        algorithm: OptimizationAlgorithm = OptimizationAlgorithm.HYBRID
    ) -> OptimizedRoute:
        """
        Résout le TSP avec l'algorithme spécifié.

        Returns:
            OptimizedRoute avec la solution optimisée
        """
        import time as time_module
        start_time = time_module.time()

        if not self.locations:
            return OptimizedRoute(
                stops=[],
                total_distance=0,
                total_duration=0,
                total_service_time=0,
                total_travel_time=0,
                total_waiting_time=0,
                optimization_score=100,
                algorithm_used=algorithm.value,
                computation_time_ms=0
            )

        # Solution initiale
        initial_tour = self.nearest_neighbor()

        if algorithm == OptimizationAlgorithm.NEAREST_NEIGHBOR:
            final_tour = initial_tour
        elif algorithm == OptimizationAlgorithm.TWO_OPT:
            final_tour = self.two_opt(initial_tour)
        elif algorithm == OptimizationAlgorithm.OR_OPT:
            final_tour = self.or_opt(initial_tour)
        elif algorithm == OptimizationAlgorithm.SIMULATED_ANNEALING:
            final_tour = self.simulated_annealing(initial_tour)
        elif algorithm == OptimizationAlgorithm.HYBRID:
            # Combinaison pour meilleurs résultats
            tour = self.two_opt(initial_tour)
            tour = self.or_opt(tour)
            final_tour = tour
        else:
            final_tour = initial_tour

        # Construit le résultat
        stops = []
        total_distance = 0
        total_travel_time = 0
        total_service_time = 0
        total_waiting_time = 0
        violations = []

        current_time_minutes = time_to_minutes(self.constraints.work_start)

        for i, idx in enumerate(final_tour):
            loc = self.all_locations[idx]

            if i > 0:
                dist = self.distance_matrix[final_tour[i-1]][idx]
                travel_time = calculate_travel_time(dist)
            else:
                dist = 0
                travel_time = 0

            total_distance += dist
            total_travel_time += travel_time
            current_time_minutes += travel_time

            # Calcul de l'attente si arrivée avant fenêtre
            waiting = 0
            if loc.time_window_start:
                window_start = time_to_minutes(loc.time_window_start)
                if current_time_minutes < window_start:
                    waiting = window_start - current_time_minutes
                    current_time_minutes = window_start

            total_waiting_time += waiting

            # Vérification contraintes
            if loc.time_window_end:
                window_end = time_to_minutes(loc.time_window_end)
                if current_time_minutes > window_end:
                    violations.append(f"Arrivée tardive à {loc.name}")

            arrival_time = minutes_to_time(current_time_minutes)

            # Service
            service = loc.service_time if idx not in [final_tour[0], final_tour[-1]] else 0
            total_service_time += service
            current_time_minutes += service

            departure_time = minutes_to_time(current_time_minutes)

            stops.append(RouteStop(
                location=loc,
                arrival_time=arrival_time,
                departure_time=departure_time,
                waiting_time=waiting,
                travel_time_from_prev=travel_time,
                distance_from_prev=dist
            ))

        end_time = time_module.time()
        computation_time_ms = int((end_time - start_time) * 1000)

        total_duration = total_travel_time + total_service_time + total_waiting_time

        # Score d'optimisation (0-100)
        # Basé sur: temps total vs théorique, violations, équilibre
        theoretical_min = total_distance / AVERAGE_SPEED_KMH * 60 + total_service_time
        efficiency = min(100, (theoretical_min / max(1, total_duration)) * 100)
        penalty = len(violations) * 10
        optimization_score = max(0, efficiency - penalty)

        return OptimizedRoute(
            stops=stops,
            total_distance=round(total_distance, 2),
            total_duration=total_duration,
            total_service_time=total_service_time,
            total_travel_time=total_travel_time,
            total_waiting_time=total_waiting_time,
            optimization_score=round(optimization_score, 2),
            algorithm_used=algorithm.value,
            computation_time_ms=computation_time_ms,
            feasible=len(violations) == 0,
            violations=violations
        )


# ============================================================================
# VRP ALGORITHMS
# ============================================================================

class VRPSolver:
    """
    Solveur VRP (Vehicle Routing Problem).

    Optimise les tournées pour plusieurs véhicules/techniciens.
    """

    def __init__(
        self,
        locations: list[Location],
        vehicles: list[tuple[str, Location, VehicleConstraints]],  # (id, depot, constraints)
    ):
        self.locations = locations
        self.vehicles = vehicles
        self.n_vehicles = len(vehicles)
        self.n_locations = len(locations)

    def savings_algorithm(self) -> VRPSolution:
        """
        Algorithme de Clarke-Wright (Savings).

        Construit des routes en fusionnant des trajets courts.
        Efficace pour le VRP avec contraintes de capacité.
        """
        import time as time_module
        start_time = time_module.time()

        if not self.locations or not self.vehicles:
            return VRPSolution(
                routes={},
                total_distance=0,
                total_duration=0,
                unassigned_locations=[],
                balance_score=100,
                overall_score=100,
                computation_time_ms=0
            )

        # Initialisation: chaque location dans sa propre route
        routes: dict[str, list[int]] = {}
        location_to_route: dict[int, str] = {}

        # Calcul des savings
        savings = []

        for v_id, depot, constraints in self.vehicles:
            routes[v_id] = []

            # Distance depuis le dépôt
            depot_distances = []
            for i, loc in enumerate(self.locations):
                dist = haversine_distance(depot.lat, depot.lng, loc.lat, loc.lng)
                depot_distances.append(dist)

            # Calcul des savings pour chaque paire de locations
            for i in range(self.n_locations):
                for j in range(i + 1, self.n_locations):
                    loc_i = self.locations[i]
                    loc_j = self.locations[j]

                    dist_ij = haversine_distance(loc_i.lat, loc_i.lng, loc_j.lat, loc_j.lng)

                    # Saving = d(depot,i) + d(depot,j) - d(i,j)
                    saving = depot_distances[i] + depot_distances[j] - dist_ij

                    if saving > 0:
                        savings.append((saving, i, j, v_id))

        # Tri par savings décroissants
        savings.sort(reverse=True, key=lambda x: x[0])

        # Assignation initiale: round-robin
        vehicle_ids = [v[0] for v in self.vehicles]
        for i, loc in enumerate(self.locations):
            v_id = vehicle_ids[i % self.n_vehicles]
            routes[v_id].append(i)
            location_to_route[i] = v_id

        # Fusion des routes basée sur les savings
        for saving, i, j, preferred_vehicle in savings:
            v_i = location_to_route.get(i)
            v_j = location_to_route.get(j)

            if v_i is None or v_j is None or v_i == v_j:
                continue

            route_i = routes[v_i]
            route_j = routes[v_j]

            # Vérifie si i est à une extrémité de sa route
            # et j est à une extrémité de sa route
            if not route_i or not route_j:
                continue

            # Fusion possible si les deux sont aux extrémités
            if route_i[-1] == i and route_j[0] == j:
                # Fusionne route_j à la fin de route_i
                merged = route_i + route_j

                # Vérifie contraintes
                v_idx = next(idx for idx, v in enumerate(self.vehicles) if v[0] == v_i)
                _, depot, constraints = self.vehicles[v_idx]

                if self._is_route_feasible(merged, depot, constraints):
                    routes[v_i] = merged
                    routes[v_j] = []
                    for loc_idx in route_j:
                        location_to_route[loc_idx] = v_i

        # Optimisation locale de chaque route avec 2-opt
        optimized_routes: dict[str, OptimizedRoute] = {}
        total_distance = 0
        total_duration = 0
        unassigned = []

        for v_id, depot, constraints in self.vehicles:
            route_indices = routes[v_id]

            if not route_indices:
                optimized_routes[v_id] = OptimizedRoute(
                    stops=[],
                    total_distance=0,
                    total_duration=0,
                    total_service_time=0,
                    total_travel_time=0,
                    total_waiting_time=0,
                    optimization_score=100,
                    algorithm_used="savings",
                    computation_time_ms=0
                )
                continue

            route_locations = [self.locations[i] for i in route_indices]

            solver = TSPSolver(
                locations=route_locations,
                depot=depot,
                constraints=constraints
            )

            optimized = solver.solve(OptimizationAlgorithm.HYBRID)
            optimized_routes[v_id] = optimized
            total_distance += optimized.total_distance
            total_duration += optimized.total_duration

        end_time = time_module.time()
        computation_time_ms = int((end_time - start_time) * 1000)

        # Calcul du score d'équilibre
        durations = [r.total_duration for r in optimized_routes.values() if r.total_duration > 0]
        if durations:
            avg_duration = sum(durations) / len(durations)
            variance = sum((d - avg_duration) ** 2 for d in durations) / len(durations)
            std_dev = math.sqrt(variance)
            balance_score = max(0, 100 - (std_dev / max(1, avg_duration) * 100))
        else:
            balance_score = 100

        # Score global
        scores = [r.optimization_score for r in optimized_routes.values()]
        avg_score = sum(scores) / len(scores) if scores else 100
        overall_score = (avg_score + balance_score) / 2

        return VRPSolution(
            routes=optimized_routes,
            total_distance=round(total_distance, 2),
            total_duration=total_duration,
            unassigned_locations=unassigned,
            balance_score=round(balance_score, 2),
            overall_score=round(overall_score, 2),
            computation_time_ms=computation_time_ms
        )

    def _is_route_feasible(
        self,
        route: list[int],
        depot: Location,
        constraints: VehicleConstraints
    ) -> bool:
        """Vérifie si une route est réalisable."""
        if not route:
            return True

        # Calcul distance totale
        total_distance = 0
        prev_lat, prev_lng = depot.lat, depot.lng

        for idx in route:
            loc = self.locations[idx]
            total_distance += haversine_distance(prev_lat, prev_lng, loc.lat, loc.lng)
            prev_lat, prev_lng = loc.lat, loc.lng

        # Retour au dépôt
        total_distance += haversine_distance(prev_lat, prev_lng, depot.lat, depot.lng)

        if total_distance > constraints.max_distance_km:
            return False

        # Temps total
        total_time = calculate_travel_time(total_distance)
        total_time += sum(self.locations[idx].service_time for idx in route)

        if total_time > constraints.max_duration_minutes:
            return False

        # Capacité
        total_weight = sum(self.locations[idx].weight for idx in route)
        total_volume = sum(self.locations[idx].volume for idx in route)

        if total_weight > constraints.max_weight or total_volume > constraints.max_volume:
            return False

        return True


# ============================================================================
# SERVICE CLASS
# ============================================================================

class RouteOptimizationService:
    """
    Service d'optimisation des tournées pour le module Field Service.

    Intègre les solveurs TSP/VRP avec la base de données AZALS.
    """

    def __init__(self, db: Session, tenant_id: str):
        self.db = db
        self.tenant_id = tenant_id

    def optimize_route(
        self,
        technician_id: uuid.UUID,
        route_date: date,
        algorithm: OptimizationAlgorithm = OptimizationAlgorithm.HYBRID,
        depot_lat: float | None = None,
        depot_lng: float | None = None
    ) -> OptimizedRoute:
        """
        Optimise la tournée d'un technicien pour une date donnée.

        Args:
            technician_id: ID du technicien
            route_date: Date de la tournée
            algorithm: Algorithme à utiliser
            depot_lat/lng: Point de départ (si différent du domicile)

        Returns:
            OptimizedRoute avec l'ordre optimisé des interventions
        """
        # Récupère les interventions planifiées
        interventions = self.db.query(Intervention).filter(
            Intervention.tenant_id == self.tenant_id,
            Intervention.technician_id == technician_id,
            Intervention.scheduled_date == route_date,
            Intervention.status.notin_([
                InterventionStatus.CANCELLED,
                InterventionStatus.FAILED,
                InterventionStatus.COMPLETED
            ])
        ).all()

        if not interventions:
            return OptimizedRoute(
                stops=[],
                total_distance=0,
                total_duration=0,
                total_service_time=0,
                total_travel_time=0,
                total_waiting_time=0,
                optimization_score=100,
                algorithm_used=algorithm.value,
                computation_time_ms=0
            )

        # Récupère le technicien pour les contraintes
        technician = self.db.query(Technician).filter(
            Technician.id == technician_id,
            Technician.tenant_id == self.tenant_id
        ).first()

        # Construit les locations
        locations = []
        for interv in interventions:
            if interv.address_lat and interv.address_lng:
                loc = Location(
                    id=str(interv.id),
                    name=interv.title or interv.reference,
                    lat=float(interv.address_lat),
                    lng=float(interv.address_lng),
                    time_window_start=interv.scheduled_time_start,
                    time_window_end=interv.scheduled_time_end,
                    service_time=interv.estimated_duration or DEFAULT_SERVICE_TIME,
                    priority=self._priority_to_int(interv.priority)
                )
                locations.append(loc)

        if not locations:
            return OptimizedRoute(
                stops=[],
                total_distance=0,
                total_duration=0,
                total_service_time=0,
                total_travel_time=0,
                total_waiting_time=0,
                optimization_score=0,
                algorithm_used=algorithm.value,
                computation_time_ms=0,
                feasible=False,
                violations=["Aucune intervention avec coordonnées GPS"]
            )

        # Point de départ (dépôt)
        if depot_lat and depot_lng:
            depot = Location(
                id="depot",
                name="Dépôt",
                lat=depot_lat,
                lng=depot_lng
            )
        elif technician and technician.last_location_lat and technician.last_location_lng:
            depot = Location(
                id="depot",
                name="Position actuelle",
                lat=float(technician.last_location_lat),
                lng=float(technician.last_location_lng)
            )
        else:
            # Utilise la première intervention comme point de départ
            depot = None

        # Contraintes
        constraints = VehicleConstraints(
            max_duration_minutes=technician.max_daily_interventions * 60 if technician else 480
        )

        if technician and technician.working_hours:
            # Parse les heures de travail
            today_name = route_date.strftime("%a").lower()[:3]
            if today_name in technician.working_hours:
                hours = technician.working_hours[today_name]
                if "start" in hours:
                    h, m = map(int, hours["start"].split(":"))
                    constraints.work_start = time(h, m)
                if "end" in hours:
                    h, m = map(int, hours["end"].split(":"))
                    constraints.work_end = time(h, m)

        # Résout le TSP
        solver = TSPSolver(locations, depot, constraints)
        result = solver.solve(algorithm)

        return result

    def optimize_multiple_routes(
        self,
        route_date: date,
        technician_ids: list[uuid.UUID] | None = None,
        rebalance: bool = True
    ) -> VRPSolution:
        """
        Optimise les tournées de plusieurs techniciens (VRP).

        Args:
            route_date: Date des tournées
            technician_ids: Liste des techniciens (tous si None)
            rebalance: Rééquilibrer la charge entre techniciens

        Returns:
            VRPSolution avec les tournées optimisées
        """
        # Récupère les techniciens actifs
        query = self.db.query(Technician).filter(
            Technician.tenant_id == self.tenant_id,
            Technician.is_active == True
        )

        if technician_ids:
            query = query.filter(Technician.id.in_(technician_ids))

        technicians = query.all()

        if not technicians:
            return VRPSolution(
                routes={},
                total_distance=0,
                total_duration=0,
                unassigned_locations=[],
                balance_score=100,
                overall_score=100,
                computation_time_ms=0
            )

        # Récupère toutes les interventions
        interventions = self.db.query(Intervention).filter(
            Intervention.tenant_id == self.tenant_id,
            Intervention.scheduled_date == route_date,
            Intervention.status.notin_([
                InterventionStatus.CANCELLED,
                InterventionStatus.FAILED,
                InterventionStatus.COMPLETED
            ])
        ).all()

        if not interventions:
            return VRPSolution(
                routes={str(t.id): OptimizedRoute(
                    stops=[], total_distance=0, total_duration=0,
                    total_service_time=0, total_travel_time=0, total_waiting_time=0,
                    optimization_score=100, algorithm_used="none", computation_time_ms=0
                ) for t in technicians},
                total_distance=0,
                total_duration=0,
                unassigned_locations=[],
                balance_score=100,
                overall_score=100,
                computation_time_ms=0
            )

        # Construit les locations
        locations = []
        for interv in interventions:
            if interv.address_lat and interv.address_lng:
                loc = Location(
                    id=str(interv.id),
                    name=interv.title or interv.reference,
                    lat=float(interv.address_lat),
                    lng=float(interv.address_lng),
                    time_window_start=interv.scheduled_time_start,
                    time_window_end=interv.scheduled_time_end,
                    service_time=interv.estimated_duration or DEFAULT_SERVICE_TIME,
                    priority=self._priority_to_int(interv.priority)
                )
                locations.append(loc)

        # Construit les véhicules
        vehicles = []
        for tech in technicians:
            if tech.last_location_lat and tech.last_location_lng:
                depot = Location(
                    id=f"depot_{tech.id}",
                    name=f"Départ {tech.first_name}",
                    lat=float(tech.last_location_lat),
                    lng=float(tech.last_location_lng)
                )
            else:
                # Position par défaut (Paris)
                depot = Location(
                    id=f"depot_{tech.id}",
                    name=f"Départ {tech.first_name}",
                    lat=48.8566,
                    lng=2.3522
                )

            constraints = VehicleConstraints(
                max_duration_minutes=tech.max_daily_interventions * 60 if tech.max_daily_interventions else 480
            )

            vehicles.append((str(tech.id), depot, constraints))

        # Résout le VRP
        solver = VRPSolver(locations, vehicles)
        return solver.savings_algorithm()

    def apply_optimization(
        self,
        technician_id: uuid.UUID,
        route_date: date,
        optimized_route: OptimizedRoute
    ) -> Route:
        """
        Applique une optimisation à la base de données.

        Met à jour l'ordre des interventions et crée/met à jour la Route.
        """
        # Cherche ou crée la Route
        route = self.db.query(Route).filter(
            Route.tenant_id == self.tenant_id,
            Route.technician_id == technician_id,
            Route.route_date == route_date
        ).first()

        if not route:
            route = Route(
                tenant_id=self.tenant_id,
                technician_id=technician_id,
                route_date=route_date
            )
            self.db.add(route)

        # Met à jour les informations
        intervention_order = [stop.location.id for stop in optimized_route.stops
                            if stop.location.id != "depot"]

        route.intervention_order = intervention_order
        route.is_optimized = True
        route.optimization_score = Decimal(str(optimized_route.optimization_score))
        route.planned_distance = Decimal(str(optimized_route.total_distance))
        route.planned_duration = optimized_route.total_duration
        route.planned_interventions = len(intervention_order)

        if optimized_route.stops:
            first_stop = optimized_route.stops[0]
            last_stop = optimized_route.stops[-1]

            route.start_lat = Decimal(str(first_stop.location.lat))
            route.start_lng = Decimal(str(first_stop.location.lng))
            route.start_location = first_stop.location.name
            route.start_time = first_stop.arrival_time

            route.end_lat = Decimal(str(last_stop.location.lat))
            route.end_lng = Decimal(str(last_stop.location.lng))
            route.end_location = last_stop.location.name
            route.end_time = last_stop.departure_time

        self.db.commit()
        self.db.refresh(route)

        return route

    def get_optimization_preview(
        self,
        technician_id: uuid.UUID,
        route_date: date
    ) -> dict:
        """
        Retourne une prévisualisation de l'optimisation sans l'appliquer.

        Utile pour l'interface utilisateur avant validation.
        """
        # Optimisation actuelle
        current = self.optimize_route(
            technician_id, route_date,
            algorithm=OptimizationAlgorithm.NEAREST_NEIGHBOR
        )

        # Optimisation améliorée
        optimized = self.optimize_route(
            technician_id, route_date,
            algorithm=OptimizationAlgorithm.HYBRID
        )

        # Calcul des gains
        distance_saved = current.total_distance - optimized.total_distance
        time_saved = current.total_duration - optimized.total_duration

        return {
            "current": {
                "distance_km": current.total_distance,
                "duration_minutes": current.total_duration,
                "stops": len(current.stops),
                "score": current.optimization_score
            },
            "optimized": {
                "distance_km": optimized.total_distance,
                "duration_minutes": optimized.total_duration,
                "stops": len(optimized.stops),
                "score": optimized.optimization_score,
                "algorithm": optimized.algorithm_used
            },
            "savings": {
                "distance_km": round(distance_saved, 2),
                "distance_percent": round(distance_saved / max(1, current.total_distance) * 100, 1),
                "time_minutes": time_saved,
                "time_percent": round(time_saved / max(1, current.total_duration) * 100, 1)
            },
            "recommendation": "optimize" if distance_saved > 1 or time_saved > 5 else "keep_current"
        }

    def _priority_to_int(self, priority) -> int:
        """Convertit une priorité enum en entier."""
        if priority is None:
            return 3

        priority_map = {
            "emergency": 1,
            "urgent": 2,
            "high": 3,
            "normal": 4,
            "low": 5
        }

        return priority_map.get(str(priority).lower(), 3)


# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================

def estimate_route_metrics(
    locations: list[Location],
    depot: Location | None = None
) -> dict:
    """
    Estime les métriques d'une route sans optimisation complète.

    Utile pour les estimations rapides avant planification.
    """
    if not locations:
        return {
            "estimated_distance_km": 0,
            "estimated_duration_minutes": 0,
            "service_time_minutes": 0,
            "travel_time_minutes": 0,
            "num_stops": 0
        }

    # Distance totale (somme des distances au plus proche)
    total_distance = 0
    total_service = sum(loc.service_time for loc in locations)

    if depot:
        current = depot
    else:
        current = locations[0]

    for loc in locations:
        if loc != current:
            dist = haversine_distance(current.lat, current.lng, loc.lat, loc.lng)
            total_distance += dist
            current = loc

    # Retour au dépôt
    if depot:
        total_distance += haversine_distance(current.lat, current.lng, depot.lat, depot.lng)

    travel_time = calculate_travel_time(total_distance)

    return {
        "estimated_distance_km": round(total_distance, 2),
        "estimated_duration_minutes": travel_time + total_service,
        "service_time_minutes": total_service,
        "travel_time_minutes": travel_time,
        "num_stops": len(locations)
    }

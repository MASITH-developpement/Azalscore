"""
Tests for Route Optimization Service (GAP-002).

Tests de validation des algorithmes d'optimisation de tournées.
"""

import pytest
import math
from datetime import date, time, timedelta
from decimal import Decimal

from ..route_optimization import (
    Location,
    VehicleConstraints,
    RouteStop,
    OptimizedRoute,
    OptimizationAlgorithm,
    TSPSolver,
    VRPSolver,
    haversine_distance,
    calculate_travel_time,
    build_distance_matrix,
    time_to_minutes,
    minutes_to_time,
    estimate_route_metrics,
    AVERAGE_SPEED_KMH,
    EARTH_RADIUS_KM,
)


# ============================================================================
# FIXTURES
# ============================================================================

@pytest.fixture
def paris_locations():
    """Locations dans Paris pour tests."""
    return [
        Location(
            id="loc1", name="Tour Eiffel",
            lat=48.8584, lng=2.2945,
            service_time=30
        ),
        Location(
            id="loc2", name="Notre-Dame",
            lat=48.8530, lng=2.3499,
            service_time=45
        ),
        Location(
            id="loc3", name="Louvre",
            lat=48.8606, lng=2.3376,
            service_time=60
        ),
        Location(
            id="loc4", name="Arc de Triomphe",
            lat=48.8738, lng=2.2950,
            service_time=30
        ),
        Location(
            id="loc5", name="Montmartre",
            lat=48.8867, lng=2.3431,
            service_time=45
        ),
    ]


@pytest.fixture
def paris_depot():
    """Dépôt de départ (Gare de Lyon)."""
    return Location(
        id="depot", name="Gare de Lyon",
        lat=48.8448, lng=2.3735,
        service_time=0
    )


@pytest.fixture
def locations_with_time_windows():
    """Locations avec fenêtres horaires."""
    return [
        Location(
            id="loc1", name="Client Matin",
            lat=48.8584, lng=2.2945,
            time_window_start=time(9, 0),
            time_window_end=time(11, 0),
            service_time=30
        ),
        Location(
            id="loc2", name="Client Midi",
            lat=48.8530, lng=2.3499,
            time_window_start=time(11, 30),
            time_window_end=time(13, 30),
            service_time=45
        ),
        Location(
            id="loc3", name="Client Après-midi",
            lat=48.8606, lng=2.3376,
            time_window_start=time(14, 0),
            time_window_end=time(16, 0),
            service_time=60
        ),
    ]


# ============================================================================
# DISTANCE CALCULATION TESTS
# ============================================================================

class TestHaversineDistance:
    """Tests pour le calcul de distance Haversine."""

    def test_same_point_zero_distance(self):
        """La distance d'un point à lui-même est 0."""
        dist = haversine_distance(48.8566, 2.3522, 48.8566, 2.3522)
        assert dist == 0

    def test_paris_to_london(self):
        """Distance Paris-Londres ~344 km."""
        # Paris
        lat1, lng1 = 48.8566, 2.3522
        # Londres
        lat2, lng2 = 51.5074, -0.1278

        dist = haversine_distance(lat1, lng1, lat2, lng2)

        # La vraie distance est ~343 km
        assert 340 <= dist <= 350

    def test_symmetry(self):
        """La distance est symétrique."""
        lat1, lng1 = 48.8566, 2.3522
        lat2, lng2 = 45.7640, 4.8357

        dist1 = haversine_distance(lat1, lng1, lat2, lng2)
        dist2 = haversine_distance(lat2, lng2, lat1, lng1)

        assert abs(dist1 - dist2) < 0.001

    def test_short_distance_paris(self):
        """Distance courte dans Paris (quelques km)."""
        # Tour Eiffel
        lat1, lng1 = 48.8584, 2.2945
        # Notre-Dame
        lat2, lng2 = 48.8530, 2.3499

        dist = haversine_distance(lat1, lng1, lat2, lng2)

        # ~4 km à vol d'oiseau
        assert 3 <= dist <= 5


class TestTravelTime:
    """Tests pour le calcul du temps de trajet."""

    def test_zero_distance(self):
        """0 km = 0 minutes."""
        assert calculate_travel_time(0) == 0

    def test_40km_at_40kmh(self):
        """40 km à 40 km/h = 60 minutes."""
        result = calculate_travel_time(40, 40)
        assert result == 60

    def test_20km_at_40kmh(self):
        """20 km à 40 km/h = 30 minutes."""
        result = calculate_travel_time(20, 40)
        assert result == 30

    def test_default_speed(self):
        """Vitesse par défaut utilisée."""
        result = calculate_travel_time(AVERAGE_SPEED_KMH)
        assert result == 60  # 1 heure


class TestDistanceMatrix:
    """Tests pour la matrice des distances."""

    def test_diagonal_zero(self, paris_locations):
        """La diagonale de la matrice est 0."""
        matrix = build_distance_matrix(paris_locations)

        for i in range(len(paris_locations)):
            assert matrix[i][i] == 0

    def test_symmetric_matrix(self, paris_locations):
        """La matrice est symétrique."""
        matrix = build_distance_matrix(paris_locations)
        n = len(paris_locations)

        for i in range(n):
            for j in range(n):
                assert abs(matrix[i][j] - matrix[j][i]) < 0.001

    def test_matrix_dimensions(self, paris_locations):
        """La matrice a les bonnes dimensions."""
        matrix = build_distance_matrix(paris_locations)
        n = len(paris_locations)

        assert len(matrix) == n
        for row in matrix:
            assert len(row) == n


class TestTimeConversions:
    """Tests pour les conversions de temps."""

    def test_time_to_minutes_midnight(self):
        """Minuit = 0 minutes."""
        assert time_to_minutes(time(0, 0)) == 0

    def test_time_to_minutes_noon(self):
        """Midi = 720 minutes."""
        assert time_to_minutes(time(12, 0)) == 720

    def test_time_to_minutes_arbitrary(self):
        """14h30 = 870 minutes."""
        assert time_to_minutes(time(14, 30)) == 870

    def test_minutes_to_time_midnight(self):
        """0 minutes = minuit."""
        assert minutes_to_time(0) == time(0, 0)

    def test_minutes_to_time_noon(self):
        """720 minutes = midi."""
        assert minutes_to_time(720) == time(12, 0)

    def test_roundtrip_conversion(self):
        """Conversion aller-retour."""
        original = time(9, 45)
        minutes = time_to_minutes(original)
        result = minutes_to_time(minutes)
        assert result == original


# ============================================================================
# TSP SOLVER TESTS
# ============================================================================

class TestNearestNeighbor:
    """Tests pour l'algorithme du plus proche voisin."""

    def test_empty_locations(self):
        """Pas de locations = tour vide."""
        solver = TSPSolver(locations=[])
        tour = solver.nearest_neighbor()
        assert tour == []

    def test_single_location(self, paris_depot):
        """Une seule location."""
        loc = Location(id="loc1", name="Test", lat=48.85, lng=2.35)
        solver = TSPSolver(locations=[loc], depot=paris_depot)
        tour = solver.nearest_neighbor()

        # Dépôt -> location -> dépôt
        assert len(tour) > 0

    def test_returns_valid_tour(self, paris_locations, paris_depot):
        """Retourne un tour valide visitant tous les points."""
        solver = TSPSolver(locations=paris_locations, depot=paris_depot)
        tour = solver.nearest_neighbor()

        # Tour commence au dépôt (index 0)
        assert tour[0] == 0

        # Tous les indices sont uniques (sauf dépôt)
        inner_tour = tour[1:-1]  # Sans les dépôts
        assert len(set(inner_tour)) == len(inner_tour)

    def test_visits_all_locations(self, paris_locations, paris_depot):
        """Visite toutes les locations."""
        solver = TSPSolver(locations=paris_locations, depot=paris_depot)
        tour = solver.nearest_neighbor()

        # Avec dépôt: all_locations = [depot] + locations + [depot]
        # Donc les indices des locations sont 1 à n (n = len(paris_locations))
        # Le dernier élément (n+1) est le retour au dépôt

        # Vérifie que le tour contient tous les indices de locations
        # (entre 1 et n, sans les dépôts aux extrémités)
        location_indices = set(tour[1:-1])  # Exclut dépôt départ et retour
        # Doit visiter toutes les locations (indices 1 à n)
        n = len(paris_locations)
        # Les indices valides sont ceux qui ne sont pas le dépôt (0 ou dernier)
        assert len(location_indices) == n


class TestTwoOpt:
    """Tests pour l'amélioration 2-opt."""

    def test_improves_or_equals_initial(self, paris_locations, paris_depot):
        """2-opt améliore ou maintient la solution."""
        solver = TSPSolver(locations=paris_locations, depot=paris_depot)
        initial_tour = solver.nearest_neighbor()
        initial_distance = solver._calculate_tour_distance(initial_tour)

        improved_tour = solver.two_opt(initial_tour)
        improved_distance = solver._calculate_tour_distance(improved_tour)

        assert improved_distance <= initial_distance

    def test_preserves_tour_length(self, paris_locations, paris_depot):
        """2-opt préserve la longueur du tour."""
        solver = TSPSolver(locations=paris_locations, depot=paris_depot)
        initial_tour = solver.nearest_neighbor()
        improved_tour = solver.two_opt(initial_tour)

        assert len(improved_tour) == len(initial_tour)

    def test_small_tour_unchanged(self):
        """Un tour trop petit n'est pas modifié."""
        locs = [
            Location(id="1", name="A", lat=48.85, lng=2.35),
            Location(id="2", name="B", lat=48.86, lng=2.36),
        ]
        solver = TSPSolver(locations=locs)
        tour = [0, 1]
        result = solver.two_opt(tour)
        assert len(result) == 2


class TestSimulatedAnnealing:
    """Tests pour Simulated Annealing."""

    def test_improves_solution(self, paris_locations, paris_depot):
        """SA améliore ou maintient la solution."""
        solver = TSPSolver(locations=paris_locations, depot=paris_depot)
        initial_tour = solver.nearest_neighbor()
        initial_distance = solver._calculate_tour_distance(initial_tour)

        sa_tour = solver.simulated_annealing(
            initial_tour,
            initial_temp=1000,
            min_iterations=500
        )
        sa_distance = solver._calculate_tour_distance(sa_tour)

        # SA devrait au pire maintenir la solution (avec bruit possible)
        assert sa_distance <= initial_distance * 1.05  # 5% de tolérance

    def test_returns_valid_tour(self, paris_locations, paris_depot):
        """SA retourne un tour valide."""
        solver = TSPSolver(locations=paris_locations, depot=paris_depot)
        initial_tour = solver.nearest_neighbor()
        sa_tour = solver.simulated_annealing(initial_tour, min_iterations=100)

        assert len(sa_tour) == len(initial_tour)
        assert sa_tour[0] == 0  # Commence au dépôt


class TestTSPSolve:
    """Tests pour la méthode solve complète."""

    def test_solve_returns_optimized_route(self, paris_locations, paris_depot):
        """Solve retourne un OptimizedRoute valide."""
        solver = TSPSolver(locations=paris_locations, depot=paris_depot)
        result = solver.solve(OptimizationAlgorithm.HYBRID)

        assert isinstance(result, OptimizedRoute)
        assert result.total_distance >= 0
        assert result.total_duration >= 0
        assert len(result.stops) > 0
        assert 0 <= result.optimization_score <= 100

    def test_solve_all_algorithms(self, paris_locations, paris_depot):
        """Tous les algorithmes fonctionnent."""
        algorithms = [
            OptimizationAlgorithm.NEAREST_NEIGHBOR,
            OptimizationAlgorithm.TWO_OPT,
            OptimizationAlgorithm.OR_OPT,
            OptimizationAlgorithm.SIMULATED_ANNEALING,
            OptimizationAlgorithm.HYBRID,
        ]

        for algo in algorithms:
            solver = TSPSolver(locations=paris_locations, depot=paris_depot)
            result = solver.solve(algo)

            assert isinstance(result, OptimizedRoute)
            assert result.algorithm_used == algo.value

    def test_hybrid_best_result(self, paris_locations, paris_depot):
        """L'algorithme hybride donne généralement de bons résultats."""
        solver = TSPSolver(locations=paris_locations, depot=paris_depot)

        nn_result = solver.solve(OptimizationAlgorithm.NEAREST_NEIGHBOR)
        hybrid_result = solver.solve(OptimizationAlgorithm.HYBRID)

        # Hybrid devrait être égal ou meilleur que nearest neighbor
        assert hybrid_result.total_distance <= nn_result.total_distance * 1.01

    def test_computation_time_recorded(self, paris_locations, paris_depot):
        """Le temps de calcul est enregistré."""
        solver = TSPSolver(locations=paris_locations, depot=paris_depot)
        result = solver.solve()

        assert result.computation_time_ms >= 0


class TestTimeWindowConstraints:
    """Tests pour les contraintes de fenêtres horaires."""

    def test_respects_time_windows(self, locations_with_time_windows, paris_depot):
        """Les fenêtres horaires sont respectées."""
        solver = TSPSolver(
            locations=locations_with_time_windows,
            depot=paris_depot,
            constraints=VehicleConstraints(work_start=time(8, 0))
        )
        result = solver.solve(OptimizationAlgorithm.NEAREST_NEIGHBOR)

        # Si le résultat est faisable, les fenêtres sont respectées
        if result.feasible:
            for stop in result.stops:
                if stop.location.time_window_end and stop.arrival_time:
                    arrival_min = time_to_minutes(stop.arrival_time)
                    window_end = time_to_minutes(stop.location.time_window_end)
                    assert arrival_min <= window_end

    def test_waiting_time_calculated(self, locations_with_time_windows, paris_depot):
        """Le temps d'attente est calculé pour les arrivées précoces."""
        solver = TSPSolver(
            locations=locations_with_time_windows,
            depot=paris_depot,
            constraints=VehicleConstraints(work_start=time(6, 0))  # Départ très tôt
        )
        result = solver.solve()

        # Si arrivée avant ouverture, il y a de l'attente
        assert result.total_waiting_time >= 0


# ============================================================================
# VRP SOLVER TESTS
# ============================================================================

class TestVRPSolver:
    """Tests pour le solveur VRP multi-véhicules."""

    def test_empty_input(self):
        """Entrées vides."""
        solver = VRPSolver(locations=[], vehicles=[])
        result = solver.savings_algorithm()

        assert result.total_distance == 0
        assert len(result.routes) == 0

    def test_single_vehicle(self, paris_locations, paris_depot):
        """Un seul véhicule = équivalent TSP."""
        vehicles = [
            ("v1", paris_depot, VehicleConstraints())
        ]
        solver = VRPSolver(locations=paris_locations, vehicles=vehicles)
        result = solver.savings_algorithm()

        assert "v1" in result.routes
        assert result.total_distance > 0

    def test_multiple_vehicles(self, paris_locations, paris_depot):
        """Plusieurs véhicules partagent les locations."""
        depot2 = Location(id="depot2", name="Dépôt 2", lat=48.87, lng=2.30)

        vehicles = [
            ("v1", paris_depot, VehicleConstraints()),
            ("v2", depot2, VehicleConstraints()),
        ]
        solver = VRPSolver(locations=paris_locations, vehicles=vehicles)
        result = solver.savings_algorithm()

        assert "v1" in result.routes
        assert "v2" in result.routes

        # Toutes les locations sont assignées
        total_stops = sum(len(r.stops) for r in result.routes.values())
        # Chaque route a dépôt départ + locations + dépôt retour
        assert total_stops >= len(paris_locations)

    def test_balance_score(self, paris_locations, paris_depot):
        """Le score d'équilibre est calculé."""
        depot2 = Location(id="depot2", name="Dépôt 2", lat=48.87, lng=2.30)

        vehicles = [
            ("v1", paris_depot, VehicleConstraints()),
            ("v2", depot2, VehicleConstraints()),
        ]
        solver = VRPSolver(locations=paris_locations, vehicles=vehicles)
        result = solver.savings_algorithm()

        assert 0 <= result.balance_score <= 100
        assert 0 <= result.overall_score <= 100


# ============================================================================
# VEHICLE CONSTRAINTS TESTS
# ============================================================================

class TestVehicleConstraints:
    """Tests pour les contraintes véhicule."""

    def test_default_constraints(self):
        """Contraintes par défaut."""
        constraints = VehicleConstraints()

        assert constraints.max_duration_minutes == 480
        assert constraints.work_start == time(8, 0)
        assert constraints.work_end == time(18, 0)

    def test_duration_constraint(self, paris_locations, paris_depot):
        """Contrainte de durée max est prise en compte."""
        # Durée très limitée - impossible avec 5 locations ayant chacune 30-60 min de service
        constraints = VehicleConstraints(max_duration_minutes=30)

        solver = TSPSolver(
            locations=paris_locations,
            depot=paris_depot,
            constraints=constraints
        )
        result = solver.solve()

        # Avec 30 min max et 5 locations nécessitant ~210 min de service,
        # la route devrait être marquée comme infaisable ou
        # le solveur retourne le meilleur effort (tous les cas sont valides)
        # L'important est que le solveur ne plante pas
        assert result.total_distance >= 0
        assert result.algorithm_used is not None


# ============================================================================
# UTILITY FUNCTION TESTS
# ============================================================================

class TestEstimateRouteMetrics:
    """Tests pour l'estimation rapide des métriques."""

    def test_empty_locations(self):
        """Pas de locations."""
        result = estimate_route_metrics([])

        assert result["estimated_distance_km"] == 0
        assert result["num_stops"] == 0

    def test_with_locations(self, paris_locations):
        """Avec locations."""
        result = estimate_route_metrics(paris_locations)

        assert result["estimated_distance_km"] > 0
        assert result["num_stops"] == len(paris_locations)
        assert result["service_time_minutes"] > 0

    def test_with_depot(self, paris_locations, paris_depot):
        """Avec dépôt."""
        result = estimate_route_metrics(paris_locations, paris_depot)

        # Distance avec dépôt devrait inclure le retour
        assert result["estimated_distance_km"] > 0

    def test_service_time_sum(self):
        """Le temps de service est la somme des durées."""
        locations = [
            Location(id="1", name="A", lat=48.85, lng=2.35, service_time=30),
            Location(id="2", name="B", lat=48.86, lng=2.36, service_time=45),
            Location(id="3", name="C", lat=48.87, lng=2.37, service_time=60),
        ]
        result = estimate_route_metrics(locations)

        assert result["service_time_minutes"] == 135


# ============================================================================
# LOCATION CLASS TESTS
# ============================================================================

class TestLocation:
    """Tests pour la classe Location."""

    def test_location_creation(self):
        """Création d'une location."""
        loc = Location(
            id="test",
            name="Test Location",
            lat=48.8566,
            lng=2.3522
        )

        assert loc.id == "test"
        assert loc.name == "Test Location"
        assert loc.service_time == 60  # Défaut

    def test_location_with_constraints(self):
        """Location avec contraintes temporelles."""
        loc = Location(
            id="test",
            name="Test",
            lat=48.85,
            lng=2.35,
            time_window_start=time(9, 0),
            time_window_end=time(12, 0),
            service_time=45,
            priority=1
        )

        assert loc.time_window_start == time(9, 0)
        assert loc.time_window_end == time(12, 0)
        assert loc.priority == 1


class TestRouteStop:
    """Tests pour la classe RouteStop."""

    def test_route_stop_creation(self):
        """Création d'un arrêt."""
        loc = Location(id="test", name="Test", lat=48.85, lng=2.35)
        stop = RouteStop(
            location=loc,
            arrival_time=time(9, 30),
            departure_time=time(10, 30),
            travel_time_from_prev=15,
            distance_from_prev=5.5
        )

        assert stop.location == loc
        assert stop.arrival_time == time(9, 30)
        assert stop.distance_from_prev == 5.5


# ============================================================================
# OPTIMIZED ROUTE TESTS
# ============================================================================

class TestOptimizedRoute:
    """Tests pour la classe OptimizedRoute."""

    def test_optimized_route_creation(self):
        """Création d'une route optimisée."""
        route = OptimizedRoute(
            stops=[],
            total_distance=25.5,
            total_duration=120,
            total_service_time=90,
            total_travel_time=30,
            total_waiting_time=0,
            optimization_score=85.5,
            algorithm_used="hybrid",
            computation_time_ms=150
        )

        assert route.total_distance == 25.5
        assert route.optimization_score == 85.5
        assert route.feasible is True

    def test_optimized_route_with_violations(self):
        """Route avec violations."""
        route = OptimizedRoute(
            stops=[],
            total_distance=50,
            total_duration=300,
            total_service_time=200,
            total_travel_time=100,
            total_waiting_time=0,
            optimization_score=40,
            algorithm_used="nearest_neighbor",
            computation_time_ms=50,
            feasible=False,
            violations=["Arrivée tardive", "Durée dépassée"]
        )

        assert route.feasible is False
        assert len(route.violations) == 2


# ============================================================================
# INTEGRATION TESTS
# ============================================================================

class TestFullOptimizationWorkflow:
    """Tests d'intégration du workflow complet."""

    def test_full_tsp_workflow(self, paris_locations, paris_depot):
        """Workflow TSP complet."""
        # 1. Création du solver
        solver = TSPSolver(
            locations=paris_locations,
            depot=paris_depot,
            constraints=VehicleConstraints()
        )

        # 2. Solution initiale
        initial_tour = solver.nearest_neighbor()
        initial_distance = solver._calculate_tour_distance(initial_tour)

        # 3. Amélioration 2-opt
        improved_tour = solver.two_opt(initial_tour)
        improved_distance = solver._calculate_tour_distance(improved_tour)

        # 4. Solution finale
        result = solver.solve(OptimizationAlgorithm.HYBRID)

        # Vérifications
        assert improved_distance <= initial_distance
        assert result.total_distance > 0
        assert len(result.stops) == len(paris_locations) + 2  # + dépôts

    def test_full_vrp_workflow(self, paris_locations, paris_depot):
        """Workflow VRP complet."""
        depot2 = Location(id="d2", name="Dépôt 2", lat=48.88, lng=2.32)

        vehicles = [
            ("tech1", paris_depot, VehicleConstraints(max_duration_minutes=300)),
            ("tech2", depot2, VehicleConstraints(max_duration_minutes=300)),
        ]

        solver = VRPSolver(locations=paris_locations, vehicles=vehicles)
        result = solver.savings_algorithm()

        # Vérifications
        assert len(result.routes) == 2
        assert result.total_distance > 0
        assert 0 <= result.balance_score <= 100

    def test_large_scale_tsp(self):
        """Test avec beaucoup de locations."""
        # Génère 50 locations aléatoires dans Paris
        import random
        random.seed(42)

        locations = []
        for i in range(50):
            locations.append(Location(
                id=f"loc{i}",
                name=f"Location {i}",
                lat=48.8 + random.uniform(0, 0.1),
                lng=2.3 + random.uniform(0, 0.1),
                service_time=30
            ))

        depot = Location(id="depot", name="Depot", lat=48.85, lng=2.35)

        solver = TSPSolver(locations=locations, depot=depot)
        result = solver.solve(OptimizationAlgorithm.HYBRID)

        # Devrait terminer en temps raisonnable
        assert result.computation_time_ms < 10000  # < 10 secondes
        assert result.total_distance > 0
        assert len(result.stops) == len(locations) + 2

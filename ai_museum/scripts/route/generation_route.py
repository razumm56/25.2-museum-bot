import networkx as nx
import ast
import os
from itertools import combinations
import json
import matplotlib.pyplot as plt
import cv2
import uuid
import sys
from pathlib import Path

#свой раг вставите 
from models.rag import RAGSystem


class MuseumRouteBuilder:
    def __init__(self, graph_file, background_image_path):
        self.background_image_path = background_image_path
        self.graph_file = graph_file
        with open(self.graph_file, "r", encoding="utf-8") as f:
            self.graph_data = json.load(f)
            
    def load_graph(self):
        """Загружает граф музея из JSON файла."""
        G = nx.Graph()
        for node in self.graph_data["nodes"]:
            G.add_node(node["id"], x=node["x"], y=node["y"], pos=(node["x"], node["y"]))
        for edge in self.graph_data["edges"]:
            G.add_edge(edge["from"], edge["to"], weight=edge["distance"])
        return G

    def select_optimal_nodes(self, G, nodes_list):
        """Выбирает оптимальные узлы из найденных экспонатов."""
        selected_nodes = []
        nodes_to_visit = ['0']
        node_to_entry_map = {} 

        for entry in nodes_list:
            if isinstance(entry, str) and entry.startswith('[') and entry.endswith(']'):
                entry_list = [str(x) for x in ast.literal_eval(entry)]
                best_node = self._find_best_node(G, entry_list)
                if best_node:
                    selected_nodes.append(best_node)
                    node_to_entry_map[best_node] = entry
            else:
                if G.has_node(entry):
                    selected_nodes.append(entry)
                    node_to_entry_map[entry] = entry
                    
        nodes_to_visit.extend(selected_nodes)
        return nodes_to_visit, node_to_entry_map

    def _find_best_node(self, G, nodes):
        """Находит оптимальный узел среди нескольких кандидатов."""
        best_node = None
        best_length = float('inf')
        
        for node in nodes:
            total_length = 0
            for other_node in nodes:
                if node != other_node:
                    try:
                        total_length += nx.shortest_path_length(G, source=node, target=other_node, weight='distance')
                    except nx.NetworkXNoPath:
                        total_length = float('inf')
                        break
                        
            if total_length < best_length:
                best_length = total_length
                best_node = node

        return best_node

    def _build_distance_matrix(self, G, nodes_to_visit):
        """Строит матрицу кратчайших путей между узлами."""
        shortest_paths = {}
        unreachable_pairs = []

        for u, v in combinations(nodes_to_visit, 2):
            try:
                dist = nx.shortest_path_length(G, source=u, target=v, weight='distance')
                shortest_paths[(u, v)] = dist
                shortest_paths[(v, u)] = dist
            except nx.NetworkXNoPath:
                unreachable_pairs.append((u, v))

        return shortest_paths, unreachable_pairs

    def _create_reduced_graph(self, shortest_paths, nodes_to_visit):
        """Создает упрощенный граф только с узлами для посещения."""
        G_reduced = nx.Graph()
        for node in nodes_to_visit:
            G_reduced.add_node(node)
        for (u, v), dist in shortest_paths.items():
            G_reduced.add_edge(u, v, distance=dist)
        return G_reduced

    def _solve_tsp(self, G_reduced):
        """Решает задачу коммивояжера для оптимизации маршрута."""
        initial_route = nx.approximation.traveling_salesman_problem(G_reduced, weight='distance', cycle=True)
        optimized_route = nx.approximation.simulated_annealing_tsp(
            G_reduced, weight='distance', seed=42, init_cycle=initial_route
        )
        return optimized_route

    def _expand_route(self, G, tsp_route):
        """Разворачивает маршрут, добавляя все промежуточные узлы."""
        full_path = []
        for i in range(len(tsp_route) - 1):
            try:
                segment = nx.shortest_path(G, source=tsp_route[i], target=tsp_route[i + 1], weight='distance')
                if i > 0:
                    segment = segment[1:]
                full_path.extend(segment)
            except nx.NetworkXNoPath:
                print(f"Warning: No path between {tsp_route[i]} and {tsp_route[i + 1]}")
        return full_path
    
    def _visualize_route(self, G, full_path, key_nodes):
        """Создает визуализацию маршрута на карте музея."""
        image = cv2.imread(self.background_image_path)
        image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)

        pos = nx.get_node_attributes(G, "pos")
        subgraph = nx.Graph()
        
        for i in range(len(full_path) - 1):
            u, v = full_path[i], full_path[i + 1]
            if G.has_edge(u, v):
                subgraph.add_edge(u, v)
        for node in full_path:
            subgraph.add_node(node)

        node_colors = ['#8b00ff' if node in key_nodes else '#cccccc' for node in subgraph.nodes]
        node_sizes = [200 if node in key_nodes else 100 for node in subgraph.nodes]

        output_path = f'route_{uuid.uuid4()}.jpg'

        fig, ax = plt.subplots(figsize=(12, 8))
        ax.imshow(image)
        nx.draw(subgraph, pos, ax=ax, with_labels=True, 
                node_color=node_colors, edge_color="orange",
                node_size=node_sizes, font_size=7, width=2, font_color="white")

        plt.axis('off')
        plt.savefig(output_path, dpi=300, bbox_inches='tight', pad_inches=0)
        plt.close()

        return output_path

    def build_route(self, G, retrieved_documents, k=5):
        """Строит оптимальный маршрут по музею из найденных экспонатов."""
        nodes_to_visit, node_mapping = self.select_optimal_nodes(G, retrieved_documents['nodes'])
        
        shortest_paths, unreachable = self._build_distance_matrix(G, nodes_to_visit)
        if unreachable:
            print(f"Warning: Unreachable pairs: {unreachable}")

        G_reduced = self._create_reduced_graph(shortest_paths, nodes_to_visit)
        optimized_route = self._solve_tsp(G_reduced)
        full_path = self._expand_route(G, optimized_route)
        
        print(f"Optimized route: {optimized_route}")
        print(f"Full path: {full_path}")

        image_path = self._visualize_route(G, full_path, optimized_route)

        ordered_artworks = []
        added_nodes = set()
        
        for node in optimized_route:
            if node == '0' or node in added_nodes:
                continue
                
            original_entry = node_mapping.get(node, node)
            try:
                idx = retrieved_documents['nodes'].index(original_entry)
                ordered_artworks.append({
                    "id": node,
                    "name": retrieved_documents['name'][idx],
                    "text": retrieved_documents['text'][idx],
                    "short_description": retrieved_documents['short_description'][idx],
                    "image": retrieved_documents['image'][idx]
                })
                added_nodes.add(node)
            except (ValueError, IndexError) as e:
                print(f"Warning: Could not find artwork for node {node}: {e}")

        return optimized_route, ordered_artworks, image_path

    async def generate_route(self, k, user_description, user_query):
        """Генерирует маршрут по музею на основе запроса пользователя."""
        rag = RAGSystem()
        artworks = rag.search_artworks(user_query, top_k=k)
        
        retrieved_documents = {
            'nodes': [artwork[4] for artwork in artworks],
            'name': [artwork[1] for artwork in artworks],
            'text': [artwork[2] for artwork in artworks],
            'short_description': [artwork[3] for artwork in artworks],
            'image': [artwork[6] for artwork in artworks]
        }
        
        print(f"Retrieved nodes: {retrieved_documents['nodes']}")
        
        G = self.load_graph()
        route, ordered_artworks, image_path = self.build_route(G, retrieved_documents, k)
        
        route_text = "\n\n".join([
            f"{idx}. {artwork['name']}\nЭкспонат на карте: {artwork['id']}"
            for idx, artwork in enumerate(ordered_artworks, start=1)
        ])
        
        rag.close()
        return route_text, ordered_artworks, image_path
    

route_builder = MuseumRouteBuilder('graph.json', 'route.jpg')
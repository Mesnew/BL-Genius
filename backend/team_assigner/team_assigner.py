from sklearn.cluster import KMeans
import numpy as np

class TeamAssigner:
    def __init__(self):
        # Couleurs d'équipe fixes pour l'affichage (BGR format)
        self.team_display_colors = {
            1: (0, 0, 255),      # Rouge vif (Team A)
            2: (255, 0, 0),      # Bleu vif (Team B)
        }
        # Couleurs des maillots détectées automatiquement
        self.team_colors = {}
        self.player_team_dict = {}
        self.kmeans = None
        self.team_1_centroid = None
        self.team_2_centroid = None
        self.team_1_is_dark = None  # Pour déterminer quelle équipe est foncée/claire

    def get_clustering_model(self, image):
        # Reshape the image to 2D array
        image_2d = image.reshape(-1, 3)

        # Perform K-means with 2 clusters
        kmeans = KMeans(n_clusters=2, init="k-means++", n_init=1, random_state=42)
        kmeans.fit(image_2d)

        return kmeans

    def get_player_color(self, frame, bbox):
        image = frame[int(bbox[1]):int(bbox[3]), int(bbox[0]):int(bbox[2])]

        if image.size == 0:
            return np.array([128, 128, 128])  # Gris par défaut

        top_half_image = image[0:int(image.shape[0]/2), :]

        # Get Clustering model
        kmeans = self.get_clustering_model(top_half_image)

        # Get the cluster labels for each pixel
        labels = kmeans.labels_

        # Reshape the labels to the image shape
        clustered_image = labels.reshape(top_half_image.shape[0], top_half_image.shape[1])

        # Get the player cluster (enlever les coins qui sont souvent le fond)
        corner_clusters = [clustered_image[0,0], clustered_image[0,-1], clustered_image[-1,0], clustered_image[-1,-1]]
        non_player_cluster = max(set(corner_clusters), key=corner_clusters.count)
        player_cluster = 1 - non_player_cluster

        player_color = kmeans.cluster_centers_[player_cluster]

        return player_color

    def get_color_brightness(self, color):
        """Calcule la luminosité d'une couleur (0-255)"""
        return np.mean(color)

    def assign_team_color(self, frame, player_detections):
        """Assigne les couleurs d'équipe basées sur les couleurs des maillots"""
        if len(player_detections) < 2:
            return

        player_colors = []
        for _, player_detection in player_detections.items():
            bbox = player_detection["bbox"]
            player_color = self.get_player_color(frame, bbox)
            player_colors.append(player_color)

        # Clustering en 2 équipes
        kmeans = KMeans(n_clusters=2, init="k-means++", n_init=10, random_state=42)
        kmeans.fit(player_colors)

        self.kmeans = kmeans
        self.team_1_centroid = kmeans.cluster_centers_[0]
        self.team_2_centroid = kmeans.cluster_centers_[1]

        # Déterminer quelle équipe est la plus foncée/claire
        brightness_1 = self.get_color_brightness(self.team_1_centroid)
        brightness_2 = self.get_color_brightness(self.team_2_centroid)

        # L'équipe 1 sera l'équipe la plus foncée (pour cohérence visuelle)
        if brightness_1 < brightness_2:
            self.team_1_is_dark = True
        else:
            self.team_1_is_dark = False

        # Stocker les couleurs des équipes
        self.team_colors[1] = kmeans.cluster_centers_[0]
        self.team_colors[2] = kmeans.cluster_centers_[1]

    def get_player_team(self, frame, player_bbox, player_id):
        if player_id in self.player_team_dict:
            return self.player_team_dict[player_id]

        if self.kmeans is None:
            # Si pas encore de modèle, assigner aléatoirement
            team_id = 1 if player_id % 2 == 0 else 2
            self.player_team_dict[player_id] = team_id
            return team_id

        player_color = self.get_player_color(frame, player_bbox)

        # Prédire l'équipe basée sur la distance aux centroïdes
        dist_to_team1 = np.linalg.norm(player_color - self.team_1_centroid)
        dist_to_team2 = np.linalg.norm(player_color - self.team_2_centroid)

        # Assigner à l'équipe la plus proche
        team_id = 1 if dist_to_team1 < dist_to_team2 else 2

        self.player_team_dict[player_id] = team_id

        return team_id

    def get_team_display_color(self, team_id):
        """Retourne la couleur d'affichage fixe pour une équipe"""
        return self.team_display_colors.get(team_id, (0, 255, 0))  # Vert par défaut

import pandas as pd
from sklearn.preprocessing import OneHotEncoder
from sklearn.neighbors import NearestNeighbors
import numpy as np
import pickle


class FoodRecommender:
    def __init__(self, food_data_path, model_path, encoder_path):
        # Read the Excel file from the correct path
        self.food_data = pd.read_excel(food_data_path)
        self.model_path = model_path
        self.encoder_path = encoder_path

        # Load the KNN model
        with open(self.model_path, 'rb') as model_file:
            self.knn_model = pickle.load(model_file)

        # Load the encoder
        with open(self.encoder_path, 'rb') as encoder_file:
            self.encoder = pickle.load(encoder_file)

    def recommend_similar_foods(self, dish_name, n_recommendations=5):
        dish_name = dish_name.lower()

        # Check if the dish exists in the dataset
        if dish_name not in self.food_data['Name'].str.lower().values:
            return f"Dish '{dish_name}' not found in the dataset."

        # Get the index of the dish
        dish_index = self.food_data[self.food_data['Name'].str.lower() == dish_name].index[0]

        # Get the features of the dish and transform using the encoder
        dish_features = self.encoder.transform(
            self.food_data.iloc[[dish_index]][['Ingredients', 'Flavour Profile', 'Course', 'Region', 'State']]
        )

        # Find the nearest neighbors using the KNN model
        distances, indices = self.knn_model.kneighbors(dish_features, n_neighbors=n_recommendations)

        # Get the names of the recommended dishes
        recommended_dishes = self.food_data.iloc[indices[0]]['Name'].values

        return recommended_dishes[:]


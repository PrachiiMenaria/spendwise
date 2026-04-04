import pickle
from sklearn.linear_model import LinearRegression
import numpy as np
import os

os.makedirs("models", exist_ok=True)

X = np.array([
    [10, 5],
    [20, 10],
    [30, 15]
])

y = np.array([100, 200, 300])

model = LinearRegression()
model.fit(X, y)

with open("models/model.pkl", "wb") as f:
    pickle.dump(model, f)

print("MSI model saved!")
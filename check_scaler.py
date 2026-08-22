import joblib

scaler = joblib.load("battery_model/flyintel_scaler.pkl")

print(type(scaler))

if hasattr(scaler, "feature_names_in_"):
    print("\nFeature names:")
    print(list(scaler.feature_names_in_))
else:
    print("\nScaler has no stored feature names.")

print("\nNumber of features expected:")
print(scaler.n_features_in_)

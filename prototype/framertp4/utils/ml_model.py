import joblib
import definitions

def save_model_file(model,name):
    joblib.dump(model, definitions.MLMODEL_DIR + "/" + name +".joblib")

def load_model_file(name):
    clf = joblib.load(definitions.MLMODEL_DIR + "/" + name +".joblib")
    return clf
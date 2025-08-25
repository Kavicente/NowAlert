import os
import cv2
import numpy as np
from sklearn.tree import DecisionTreeClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score
from joblib import dump
from keras.applications.vgg16 import VGG16, preprocess_input

def load_images(folder, label):
    """Load images from a folder and assign a label."""
    images = []
    labels = []
    for filename in os.listdir(folder):
        if filename.endswith('.jpg') or filename.endswith('.png'):
            img_path = os.path.join(folder, filename)
            img = cv2.imread(img_path)
            if img is not None:
                img = cv2.resize(img, (224, 224))  # Resize to match VGG16 input
                img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)  # Convert BGR to RGB
                images.append(img)
                labels.append(label)
    return images, labels

if __name__ == "__main__":
    # Define folder paths
    road_folder = 'Road_Accident'
    fire_folder = 'Fire_Incident'
    
    # Load images and assign labels (0 for Road Accident, 1 for Fire Incident)
    road_images, road_labels = load_images(road_folder, 0)
    fire_images, fire_labels = load_images(fire_folder, 1)
    
    # Combine data
    all_images = road_images + fire_images
    all_labels = road_labels + fire_labels
    
    print(f"Loaded {len(road_images)} Road Accident images and {len(fire_images)} Fire Incident images")
    
    # Convert to NumPy array
    all_images_np = np.array(all_images)
    
    # Preprocess images for VGG16
    all_images_preprocessed = preprocess_input(all_images_np)
    
    # Load VGG16 model without top layers
    base_model = VGG16(weights='imagenet', include_top=False, input_shape=(224, 224, 3))
    
    # Extract features
    features = base_model.predict(all_images_preprocessed)
    features_flattened = features.reshape(features.shape[0], -1)  # Flatten to (num_samples, 25088)
    
    # Split data into training and testing sets
    X_train, X_test, y_train, y_test = train_test_split(features_flattened, all_labels, test_size=0.2, random_state=42)
    
    # Initialize and train Decision Tree Classifier
    clf = DecisionTreeClassifier()
    clf.fit(X_train, y_train)
    
    # Evaluate the model
    y_pred = clf.predict(X_test)
    accuracy = accuracy_score(y_test, y_pred)
    print(f"Model Accuracy: {accuracy:.2f}")
    
    # Save the trained model
    dump(clf, 'emergencytypedistribution.pkl')
    print("Model saved as 'emergencytypedistribution.pkl'")
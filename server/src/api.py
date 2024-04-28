from deep_image_search import Load_Data, Search_Setup
from flask import Flask, request, jsonify
from flask_cors import CORS
import os
from werkzeug.utils import secure_filename

app = Flask(__name__)
CORS(app)  # This will enable CORS for all routes

# Global variable to store the search engine setup
search_setup = None


# Load images from a folder,
# Set up the search engine,
# Index the images
@app.route("/index", methods=["POST"])
def index_images():
    """
    Uploads the images from the folder to the server.

    Expected post request body:
    {
        "folder_path": "path to the folder"
        "image_count": "number of images to index" # Optional
    }
    route: /index

    curl -X POST -H "Content-Type: application/json" -d '{"folder_path":"/images_folder", "image_count":100}' http://localhost:5000/index
    """

    global search_setup

    try:
        data = request.get_json()
        folder_path = data["folder_path"]
        image_count = data.get("image_count")
        image_count = int(image_count) if image_count else None

        load_data = Load_Data()
        image_list = load_data.from_folder([folder_path], shuffle=True)
        search_setup = Search_Setup(image_list, image_count=image_count)
        search_setup.run_index(reindex=True)

        return jsonify({"message": "Images indexed successfully"})
    except Exception as e:
        return jsonify({"error": str(e)}), 400


# Upload the image to a temp file,
# Search for similar images to the path of the uploaded image,
# Return the matched images json
@app.route("/search", methods=["POST"])
def search_similar_images():
    """
    Search for similar images to the uploaded image.

    Expected post request body:
    {
        "image": "image file"
        "number_of_images": "number of similar images to return" # Optional
    }
    route: /search

    curl -X POST -F "image=@/path/to/image.jpg" -F "number_of_images=5" http://localhost:5000/search
    """

    global search_setup

    try:
        if "image" not in request.files:
            return jsonify({"error": "No image file in request"}), 400

        image = request.files["image"]
        number_of_images = request.form.get("number_of_images")
        number_of_images = int(number_of_images) if number_of_images else 5

        filename = secure_filename(image.filename)
        image.save(os.path.join("./data", filename))

        query_image_path = os.path.join("./data", filename)
        similar_images = search_setup.get_similar_images(
            query_image_path, number_of_images
        )
        json_response = {str(key): value for key, value in similar_images.items()}

        return jsonify(json_response)
    except Exception as e:
        return jsonify({"error": str(e)}), 400


# Search for similar images to a text query
# Return the matched images json
@app.route("/search-text", methods=["POST"])
def search_similar_images_to_text():
    """
    Search for similar images to the text query.

    Expected post request body:
    {
        "text": "text query"
        "number_of_images": "number of similar images to return" # Optional
    }
    route: /search-text

    curl -X POST -H "Content-Type: application/json" -d '{"text":"cat", "number_of_images":5}' http://localhost:5000/search-text
    """

    global search_setup

    try:
        data = request.get_json()
        text = data["text"]
        number_of_images = data.get("number_of_images")
        number_of_images = int(number_of_images) if number_of_images else 5

        similar_images = search_setup.get_similar_images_to_text(text, number_of_images)
        json_response = {str(key): str(value) for key, value in similar_images.items()}

        return jsonify(json_response)
    except Exception as e:
        return jsonify({"error": str(e)}), 400


# Cluster the vector embeddings from metadata
# Save clustered images in a clusters folder
# Caption the first 15 images in each cluster
# Get the best topic for the first 15 images in each cluster
# Rename the cluster folders to the {cluster_number}_{topic}
@app.route("/cluster", methods=["POST"])
def cluster_images():
    """
    Cluster the indexed images and save the images in each cluster to a folder.

    Expected post request body:
    {
        "n_clusters": "number of clusters"
    }
    route: /cluster
    """

    global search_setup

    try:
        data = request.get_json()
        n_clusters = data["n_clusters"]
        n_clusters = int(n_clusters)

        # Cluster the images
        search_setup.cluster_images(n_clusters)
        search_setup.save_clustered_images("./data/clusters")

        # Caption the first 15 images in each cluster
        for i in range(n_clusters):
            cluster_images = search_setup.get_clustered_images(i)
            captioned_images = search_setup.caption_images(cluster_images[:15])
            # captioned_images.to_csv(f'clusters/{i}/captions.csv', index=False)

            # Get the best topic for the first 15 images in each cluster
            best_topics = search_setup.get_best_topics(
                captioned_images["caption"].to_list()
            )
            new_folder_name = f"./data/clusters/{i}_{best_topics[0]}"
            os.rename(f"./data/clusters/{i}", new_folder_name)

        return jsonify({"message": "Images clustered successfully"})
    except Exception as e:
        return jsonify({"error": str(e)}), 400


# Get the images in a cluster by cluster number
@app.route("/get-cluster-images", methods=["POST"])
def get_cluster_images():
    """
    Get the images in a cluster by cluster number.

    Expected post request body:
    {
        "cluster_id": "cluster number"
    }
    route: /get-cluster-images
    """

    global search_setup

    try:
        data = request.get_json()
        cluster_id = data["cluster_id"]
        cluster_id = int(cluster_id)

        img_list = search_setup.get_clustered_images(cluster_id)

        return jsonify({"images": img_list})
    except Exception as e:
        return jsonify({"error": str(e)}), 400


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)

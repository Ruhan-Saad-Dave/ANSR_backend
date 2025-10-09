from flask import Flask, request, jsonify
from firebase_admin import credentials, firestore
import firebase_admin
from datetime import datetime

# --- 1. FIREBASE INITIALIZATION ---
# This service needs its own connection to Firebase.
# Make sure your 'serviceAccountKey.json' file is in the same directory.
try:
    # IMPORTANT: Replace with your actual service account key filename
    cred = credentials.Certificate("ansr-7f506-firebase-adminsdk-fbsvc-052e7ed895.json")
    firebase_admin.initialize_app(cred)
    db = firestore.client()
except Exception as e:
    print(f"Firebase initialization failed: {e}\nPlease ensure your service account key file is present and valid.")
    db = None

# --- 2. FLASK APPLICATION ---
app = Flask(__name__)


# --- 3. PENDING TRANSACTIONS API ENDPOINTS ---

@app.route('/pending', methods=['POST'])
def add_pending_item():
    """
    Adds a new pending transaction for a user.
    Expects JSON: {"UserID", "description", "amount", "type", "person_name"}
    'type' should be 'payable' (you owe) or 'receivable' (you are owed).
    """
    if not db: return jsonify({"error": "Firestore not initialized"}), 500

    data = request.get_json()
    required_fields = ["UserID", "description", "amount", "type", "person_name"]
    if not data or not all(field in data for field in required_fields):
        return jsonify({"error": "Missing required fields: UserID, description, amount, type, person_name"}), 400

    user_id = data["UserID"]

    new_item = {
        "description": data["description"],
        "amount": float(data["amount"]),
        "type": data["type"],
        "person_name": data["person_name"],
        "created_at": firestore.SERVER_TIMESTAMP
    }

    try:
        update_time, doc_ref = db.collection('Pending').document(user_id).collection('pending_items').add(new_item)

        # Replace the server timestamp with a string for the JSON response to avoid serialization error
        return jsonify({"status": "success", "id": doc_ref.id}), 201
    except Exception as e:
        return jsonify({"error": f"Failed to add pending item: {e}"}), 500


@app.route('/pending/<user_id>', methods=['GET'])
def get_pending_items(user_id):
    """
    Retrieves all pending items for a given UserID.
    """
    if not db: return jsonify({"error": "Firestore not initialized"}), 500

    try:
        items_ref = db.collection('Pending').document(user_id).collection('pending_items').stream()

        pending_list = []
        for item in items_ref:
            item_data = item.to_dict()
            item_data['id'] = item.id
            pending_list.append(item_data)

        return jsonify(pending_list)
    except Exception as e:
        return jsonify({"error": f"Failed to retrieve items: {e}"}), 500


@app.route('/pending/<user_id>/<item_id>', methods=['DELETE'])
def delete_pending_item(user_id, item_id):
    """
    Deletes a specific pending item by its ID.
    """
    if not db: return jsonify({"error": "Firestore not initialized"}), 500

    try:
        db.collection('Pending').document(user_id).collection('pending_items').document(item_id).delete()
        return jsonify({"success": True, "message": f"Item {item_id} deleted successfully."})
    except Exception as e:
        return jsonify({"error": f"Failed to delete item: {e}"}), 500


# --- 4. MAIN EXECUTION BLOCK ---
if __name__ == '__main__':
    # Running on port 5001 to avoid conflicts with your main parsing app (on port 5000)
    app.run(debug=True)

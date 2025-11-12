from flask import Flask, request, jsonify
from core.setup import initialize_firebase  # Using your custom initializer

# Note: datetime is no longer needed as Supabase handles timestamps

# --- 1. SUPABASE INITIALIZATION ---
# Initialize the Supabase client using your custom function
db = initialize_firebase()

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
    if not db: return jsonify({"error": "Supabase not initialized"}), 500

    data = request.get_json()
    required_fields = ["UserID", "description", "amount", "type", "person_name"]
    if not data or not all(field in data for field in required_fields):
        return jsonify({"error": "Missing required fields: UserID, description, amount, type, person_name"}), 400

    user_id = data["UserID"]

    # --- Map incoming JSON to your Supabase schema ---
    try:
        new_item = {
            "user_id": user_id,
            "reason": data["description"],
            "amount": float(data["amount"]),
            # Map 'type' to the 'to_give' boolean
            "to_give": True if data["type"] == 'payable' else False,
            "other_user": data["person_name"]
            # 'created_at' and 'pending_id' are handled automatically by Supabase
        }
    except ValueError:
        return jsonify({"error": "Invalid amount. Must be a number."}), 400

    try:
        # Insert the new record into the 'pending' table
        response = db.table('pending').insert(new_item).execute()

        if not response.data:
            raise Exception("Failed to insert data or no data returned.")

        # Get the new ID from the returned data
        new_id = response.data[0]['pending_id']

        return jsonify({"status": "success", "id": new_id}), 201
    except Exception as e:
        return jsonify({"error": f"Failed to add pending item: {e}"}), 500


@app.route('/pending/<user_id>', methods=['GET'])
def get_pending_items(user_id):
    """
    Retrieves all pending items for a given UserID.
    """
    if not db: return jsonify({"error": "Supabase not initialized"}), 500

    try:
        # Select all items from 'pending' table for the user
        response = db.table('pending').select('*').eq('user_id', user_id).execute()

        pending_list = []

        # --- Map Supabase columns back to original JSON format ---
        for item in response.data:
            pending_list.append({
                "id": item['pending_id'],
                "description": item['reason'],
                "amount": item['amount'],
                "person_name": item['other_user'],
                "type": 'payable' if item['to_give'] else 'receivable',
                "created_at": item['created_at']
            })

        return jsonify(pending_list)
    except Exception as e:
        return jsonify({"error": f"Failed to retrieve items: {e}"}), 500


@app.route('/pending/<user_id>/<item_id>', methods=['DELETE'])
def delete_pending_item(user_id, item_id):
    """
    Deletes a specific pending item by its ID.
    """
    if not db: return jsonify({"error": "Supabase not initialized"}), 500

    try:
        # Delete from 'pending' table where user_id and pending_id match
        db.table('pending').delete() \
            .eq('user_id', user_id) \
            .eq('pending_id', item_id) \
            .execute()

        return jsonify({"success": True, "message": f"Item {item_id} deleted successfully."})
    except Exception as e:
        return jsonify({"error": f"Failed to delete item: {e}"}), 500


# --- 4. MAIN EXECUTION BLOCK ---
if __name__ == '__main__':
    # Running on port 5001 (as in your original file)
    app.run(debug=True, port=5001)
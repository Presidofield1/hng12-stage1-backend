"""import os
import requests
import uuid6
from flask import Flask, jsonify, request
from flask_sqlalchemy import SQLAlchemy 
from flask_cors import CORS
from datetime import datetime, timezone


#Initialize 
app = Flask(__name__)
CORS(app)

# -- Configuration --
database_url = os.getenv("DATABASE_URL")

if database_url:
    # This replaces 'postgres://' with 'postgresql://' for SQLAlchemy compatibility
    if database_url.startswith("postgres://"):
        database_url = database_url.replace("postgres://", "postgresql://", 1)
    app.config['SQLALCHEMY_DATABASE_URI'] = database_url
else:
    # Local SQLite for development
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///profiles.db'

app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)


# --Database Model --
class Profile(db.Model):
    id = db.Column(db.String(36), primary_key=True)
    name= db.Column(db.String(100), unique=True, nullable=False)
    gender = db.Column(db.String(20))
    gender_probability = db.Column(db.Float)
    sample_size = db.Column(db.Float)
    age = db.Column(db.Integer)
    age_group = db.Column(db.String(20))
    country_id = db.Column(db.String(10))
    country_probability = db.Column (db.Float)
    created_at = db.Column(db.String(30))

    def to_dict(self, summary = False):
        data = {
            "id": self.id,
            "name": self.name,
            "gender": self.gender,
            "age": self.age,
            "age_group": self.age_group,
            "country_id": self.country_id
        }

        if not summary:
            data.update({
                "gender_probability": self.gender_probability,
                "sample_size": self.sample_size,
                "country_probability": self.country_probability,
                "created_at": self.created_at
            })
        return data
        
    
# Initialise Database
with app.app_context():
    db.create_all()

def get_external_data(name):
    try:
        # 1. Genderize
        g_url = f"https://api.genderize.io?name={name}"
        g_resp = requests.get(g_url, timeout=5).json()
        if not g_resp.get("gender") or g_resp.get("count") == 0:
            return None, "Genderize"
        
        # 2. Agify - Cleaned URL and precise check
        a_url = f"https://api.agify.io?name={name}"
        a_resp = requests.get(a_url, timeout=5).json()
        
        # DEBUG: This will print in your 'app.py' terminal
        print(f"DEBUG Agify Response: {a_resp}")

        if a_resp.get("age") is None: 
            return None, "Agify"
        
        # 3. Nationalize
        n_url = f"https://api.nationalize.io?name={name}"
        n_resp = requests.get(n_url, timeout=5).json()
        if not n_resp.get("country"):
            return None, "Nationalize"
        
        top_country = max(n_resp["country"], key=lambda x: x["probability"])
        age = a_resp["age"]
        
        if age <= 12: age_group = "child"
        elif age <= 19: age_group = "teenager"
        elif age <= 59: age_group = "adult"
        else: age_group = "senior"

        return {
            "gender": g_resp["gender"],
            "gender_probability": g_resp["probability"],
            "sample_size": g_resp["count"],
            "age": age,
            "age_group": age_group,
            "country_id": top_country["country_id"],
            "country_probability": top_country["probability"]
        }, None
    except Exception as e:
        print(f"System Error: {e}")
        return None, "System"

# -- Endpoints --

@app.route('/api/profiles', methods=['POST'])
def create_profile():
    data = request.get_json()
    if not data or 'name' not in data: #or not str(data['name']).strip():
        return jsonify({"status": "error", "message": "Missing or empty name"}), 400
    
    name = str(data['name']).strip().lower()

    # Checking for existing
    existing = Profile.query.filter_by(name=name).first()
    if existing:
        return jsonify({"status": "success", "message": "Profile already exists", "data": existing.to_dict()}), 200
    
    # Fetch from APIs
    ext_data, error_source = get_external_data(name)
    if error_source:
        return jsonify ({"status": "error", "message": f"{error_source} returned an invalid response"}), 502
    

    # Save to DB
    new_profile = Profile(
        id=str(uuid6.uuid7()),
        name = name,
        created_at = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        **ext_data
    )
    db.session.add(new_profile)
    db.session.commit()

    return jsonify({"status": "success", "data": new_profile.to_dict()}), 201


@app.route('/api/profiles', methods=['GET'])
def get_all_profiles():
    gender = request.args.get('gender')
    country = request.args.get('country_id')
    age_group= request.args.get('age_group')


    query = Profile.query
    if gender: query = query.filter(Profile.gender == gender.lower())
    if country: query = query.filter(Profile.country_id == country.upper())
    if age_group: query= query.filter(Profile.age_group == age_group.lower())

    profiles = query.all()
    return jsonify({
        "status": "success",
        "count": len(profiles),
        "data": [p.to_dict(summary = True) for p in profiles]
    }), 200

@app.route('/api/profiles/<id>', methods = ['GET'])
def get_profile(id):
    profile = db.session.get(Profile, id) #Profile.query.get(id)
    if not profile:
        return jsonify({
            "status": "error", "message": "Profile not found"}), 404
    return jsonify({
        "status": "success", "data": profile.to_dict()}), 200



@app.route('/api/profiles/<id>', methods= ['DELETE'])
def delete_profile(id):
    profile = Profile.query.get(id)
    if not profile:
        return jsonify({"status": "error", "message": "Profile not found"}), 404
    db.session.delete(profile)
    db.session.commit()
    return '', 204


if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5001))
    app.run(host='0.0.0.0', port=port)"""


#Import needed libraries

"""from flask import Flask, jsonify, request
import os
import requests
from flask_cors import CORS
from datetime import datetime, timezone

# Initialise app
app = Flask(__name__)
CORS(app)

@app.get('/api/classify')
def classify_name():
    name = request.args.get('name')

    #Check if name is Missing or Empty (400)
    if not name:
        return jsonify({"status": "error", "message": "Missing or empty name"}), 400
    
    if not isinstance(name, str) or name.isdigit():
        return jsonify({"status": "error", "message": "name is not string"}), 422
    try:
        # Call the API provided
        external_url = f"https://api.genderize.io/?name={name}"
        response = requests.get(external_url, timeout=5) # 5s timeout to keep it fast

        if response.status_code != 200:
            return jsonify({"status": "error", "message": "Upstream failure"}), 502
        
        data = response.json()

        # Cases Presented
        gender = data.get("gender")
        sample_size = data.get("count", 0)
        probability = data.get ("probability", 0.0)

        if gender is None or sample_size == 0:
            return jsonify ({"status": "error", "message": "No prediction available"})
        
        # Processing the given conditions
        is_confident = (probability >= 0.7) and (sample_size >= 100)

        #ISO 8610 UTC Timestamp
        process_time = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


        return jsonify({
            "status": "success",
            "data": {
                "name": name,
                "gender": gender,
                "probability": probability,
                "sample_size": sample_size,
                "condition": is_confident,
                "processed_time": process_time
            }
        }), 200
    
    except Exception:
        return jsonify({"status": "error", "message": "Server failure"}), 500
    
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5001))
    app.run(host="0.0.0.0", port=port)

"""



import os
import requests
import uuid6
from flask import Flask, jsonify, request
from flask_sqlalchemy import SQLAlchemy 
from flask_cors import CORS
from datetime import datetime, timezone


#Initialize 
app = Flask(__name__)
CORS(app)

# -- Configuration --
database_url = os.getenv("DATABASE_URL")

if database_url:
    # This replaces 'postgres://' with 'postgresql://' for SQLAlchemy compatibility
    if database_url.startswith("postgres://"):
        database_url = database_url.replace("postgres://", "postgresql://", 1)
    app.config['SQLALCHEMY_DATABASE_URI'] = database_url
else:
    # Local SQLite for development
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///profiles.db'

app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)


# --Database Model --
class Profile(db.Model):
    id = db.Column(db.String(36), primary_key=True)
    name= db.Column(db.String(100), unique=True, nullable=False)
    gender = db.Column(db.String(20))
    gender_probability = db.Column(db.Float)
    sample_size = db.Column(db.Float)
    age = db.Column(db.Integer)
    age_group = db.Column(db.String(20))
    country_id = db.Column(db.String(10))
    country_probability = db.Column (db.Float)
    created_at = db.Column(db.String(30))

    def to_dict(self, summary = False):
        data = {
            "id": self.id,
            "name": self.name,
            "gender": self.gender,
            "age": self.age,
            "age_group": self.age_group,
            "country_id": self.country_id
        }

        if not summary:
            data.update({
                "gender_probability": self.gender_probability,
                "sample_size": self.sample_size,
                "country_probability": self.country_probability,
                "created_at": self.created_at
            })
        return data
        
    
# Initialise Database
with app.app_context():
    db.create_all()

# -- Helper functions --

"""def get_external_data(name):
    try:
        #Genderize
        g_resp = requests.get(f"https://api.genderize.io?name={name}", timeout=5).json()
        if not g_resp.get("gender") or g_resp.get("count") == 0:
            return None, "Genderize"
        
        #Agify
        a_resp = requests.get(f"https://api.agify.io?name={name}", timeout= 5).json()
        if not a_resp.get("age") is None:
            return None, "Agify"
        
        #3. Nationalize
        n_resp = requests.get(f"https://api.nationalize.io?name={name}", timeout=5).json()
        if not n_resp.get("country"):
            return None, "Nationalize"
        

        # Logic: Highest Probability country
        top_country = max(n_resp["country"], key= lambda x: x["probability"])

        #Logic: Age Grouo
        age= a_resp["age"]
        if age <= 12: age_group = "child"
        elif age <= 19: age_group = "teenager"
        elif age <= 59: age_group ="adult"
        else: age_group = "senior"

        return {
            "gender": g_resp["gender"],
            "gender_probability": g_resp["probability"],
            "sample_size": g_resp["count"],
            "age": age,
            "age_group": age_group,
            "country_id": top_country["country_id"],
            "country_probability": top_country["probability"]


        }, None
    except Exception:
        return None, "System"
    """
def get_external_data(name):
    try:
        # 1. Genderize
        g_url = f"https://api.genderize.io?name={name}"
        g_resp = requests.get(g_url, timeout=5).json()
        if not g_resp.get("gender") or g_resp.get("count") == 0:
            return None, "Genderize"
        
        # 2. Agify - Cleaned URL and precise check
        a_url = f"https://api.agify.io?name={name}"
        a_resp = requests.get(a_url, timeout=5).json()
        
        # DEBUG: This will print in your 'app.py' terminal
        print(f"DEBUG Agify Response: {a_resp}")

        if a_resp.get("age") is None: 
            return None, "Agify"
        
        # 3. Nationalize
        n_url = f"https://api.nationalize.io?name={name}"
        n_resp = requests.get(n_url, timeout=5).json()
        if not n_resp.get("country"):
            return None, "Nationalize"
        
        top_country = max(n_resp["country"], key=lambda x: x["probability"])
        age = a_resp["age"]
        
        if age <= 12: age_group = "child"
        elif age <= 19: age_group = "teenager"
        elif age <= 59: age_group = "adult"
        else: age_group = "senior"

        return {
            "gender": g_resp["gender"],
            "gender_probability": g_resp["probability"],
            "sample_size": g_resp["count"],
            "age": age,
            "age_group": age_group,
            "country_id": top_country["country_id"],
            "country_probability": top_country["probability"]
        }, None
    except Exception as e:
        print(f"System Error: {e}")
        return None, "System"

# -- Endpoints --

@app.route('/api/profiles', methods=['POST'])
def create_profile():
    data = request.get_json()
    if not data or 'name' not in data or not str(data['name']).strip():
        return jsonify({"status": "success", "message": "Missing or empty name"}), 400
    
    name = str(data['name']).strip().lower()

    # Checking for existing
    existing = Profile.query.filter_by(name=name).first()
    if existing:
        return jsonify({"status": "success", "message": "Profile already exists", "data": existing.to_dict()}), 200
    
    # Fetch from APIs
    ext_data, error_source = get_external_data(name)
    if error_source:
        return jsonify ({"status": "error", "message": f"{error_source} returned an invalid response"}), 502
    

    # Save to DB
    new_profile = Profile(
        id=str(uuid6.uuid7()),
        name = name,
        created_at = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        **ext_data
    )
    db.session.add(new_profile)
    db.session.commit()

    return jsonify({"status": "success", "data": new_profile.to_dict()}), 201


@app.route('/api/profiles', methods=['GET'])
def get_all_profiles():
    gender = request.args.get('gender')
    country = request.args.get('country_id')
    age_group= request.args.get('age_group')


    query = Profile.query
    if gender: query = query.filter(Profile.gender == gender.lower())
    if country: query = query.filter(Profile.country_id == country.upper())
    if age_group: query= query.filter(Profile.age_group == age_group.lower())

    profiles = query.all()
    return jsonify({
        "status": "success",
        "count": len(profiles),
        "data": [p.to_dict(summary = True) for p in profiles]
    }), 200

@app.route('/api/profiles/<id>', methods = ['GET'])
def get_profile(id):
    profile = Profile.query.get(id)
    if not profile:
        return jsonify({
            "status": "error", "message": "Profile not found"}), 404
    return jsonify({
        "status": "success", "data": profile.to_dict()}), 200



@app.route('/api/profiles/<id>', methods= ['DELETE'])
def delete_profile(id):
    profile = Profile.query.get(id)
    if not profile:
        return jsonify({"status": "error", "message": "Profile not found"}), 404
    db.session.delete(profile)
    db.session.commit()
    return '', 204


if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5001))
    app.run(host='0.0.0.0', port=port)
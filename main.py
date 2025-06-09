from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import joblib
import uvicorn
import os
from fastapi.middleware.cors import CORSMiddleware
from typing import Literal
from email_validator import validate_email, EmailNotValidError
from verification import send_email
import random
from verification import send_email


# Define the User model to match the data structure you want to return
import firebase_admin
from firebase_admin import credentials, firestore

key_path = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")

cred = credentials.Certificate(key_path)
firebase_admin.initialize_app(cred)

db = firestore.client()



app = FastAPI()

# Add CORS middleware to your app
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "https://agricredscore.onrender.com"],  # Allow your frontend to make requests
    allow_credentials=True,
    allow_methods=["*"],  # Allow all HTTP methods (GET, POST, etc.)
    allow_headers=["*"],  # Allow all headers
)

# Load trained model
model = joblib.load("model.pkl")

# Input schema
class InputData(BaseModel):
    FirstName: str
    LastName: str
    Age: int
    Gender: str
    Education: str
    Marital_Status: str
    Region: str
    State: str
    Farm_Size: float
    Crop_Type: str
    Livestock_Type: str
    Livestock_Number: int
    Irrigation: str
    Crop_Cycles: int
    Technology_Use: str
    Previous_Loans: str
    Loan_Amount: float
    Repayment_Status: str
    Savings_Behavior: str
    Financial_Access: str
    Annual_Income: float
    Extension_Services: str
    Market_Distance: float
    Yield_Per_Season: float
    Input_Usage: str
    Labor: str
    Username: str  # not used for prediction, only returned
    Password: str


# Define mappings
mappings = {
    "Gender": {"Female": 0, "Male": 1},
    "Education": {"Primary": 0, "Secondary": 1, "Tertiary": 2},
    "Marital_Status": {"Divorced": 0, "Married": 1, "Single": 2},
    "Region": {
        "North Central": 0, "North East": 1, "North West": 2,
        "South East": 3, "South South": 4, "South West": 5
    },
    "State": {
        "Abia": 0, "Adamawa": 1, "Akwa Ibom": 2, "Anambra": 3, "Bauchi": 4, "Bayelsa": 5, "Benue": 6,
        "Borno": 7, "Cross River": 8, "Delta": 9, "Ebonyi": 10, "Edo": 11, "Ekiti": 12, "Enugu": 13,
        "FCT": 14, "Gombe": 15, "Imo": 16, "Jigawa": 17, "Kaduna": 18, "Kano": 19, "Katsina": 20,
        "Kebbi": 21, "Kogi": 22, "Kwara": 23, "Lagos": 24, "Nassarawa": 25, "Niger": 26, "Ogun": 27,
        "Ondo": 28, "Osun": 29, "Oyo": 30, "Plateau": 31, "Rivers": 32, "Sokoto": 33, "Taraba": 34,
        "Yobe": 35, "Zamfara": 36
    },
    "Crop_Type": {
        "Beans": 0, "Cassava": 1, "Cocoa": 2, "Cotton": 3, "Cowpea": 4, "Groundnut": 5, "Maize": 6,
        "Millet": 7, "Oil Palm": 8, "Plantain": 9, "Rice": 10, "Rubber": 11, "Sesame": 12,
        "Sorghum": 13, "Soybeans": 14, "Vegetables": 15, "Yam": 16
    },
    "Livestock_Type": {
        "Cattle": 0, "Goats": 1, "Pigs": 2, "Poultry": 3, "Sheep": 4, "nan": 5
    },
    "Irrigation": {"No": 0, "Yes": 1},
    "Technology_Use": {"No": 0, "Yes": 1},
    "Previous_Loans": {"No": 0, "Yes": 1},
    "Repayment_Status": {"Defaulted":0, "Late":1, "Paid on Time":2},
    "Savings_Behavior": {"No": 0, "Yes": 1},
    "Financial_Access": {"No": 0, "Yes": 1},
    "Extension_Services": {"No": 0, "Yes": 1},
    "Input_Usage": {"All": 0, "Some": 1, "nan": 2},
    "Labor": {"Both": 0, "Family": 1, "Hired": 2},
}

@app.get("/")
def home():
    return {"message": "API running. Go to /docs"}

@app.post("/predict")
def predict(data: InputData):
    input_dict = data.dict()
    username = input_dict.pop("Username")
    password = input_dict.pop("Password")

    # Apply mappings
    for key, map_dict in mappings.items():
        input_dict[key] = map_dict.get(input_dict[key], 0)  # default to 0

    # Convert to ordered list for model input
    model_features = [
        input_dict["Age"],
        input_dict["Gender"],
        input_dict["Education"],
        input_dict["Marital_Status"],
        input_dict["Region"],
        input_dict["State"],
        input_dict["Farm_Size"],
        input_dict["Crop_Type"],
        input_dict["Livestock_Type"],
        input_dict["Livestock_Number"],
        input_dict["Irrigation"],
        input_dict["Crop_Cycles"],
        input_dict["Technology_Use"],
        input_dict["Previous_Loans"],
        input_dict["Loan_Amount"],
        input_dict["Repayment_Status"],
        input_dict["Savings_Behavior"],
        input_dict["Financial_Access"],
        input_dict["Annual_Income"],
        input_dict["Extension_Services"],
        input_dict["Market_Distance"],
        input_dict["Yield_Per_Season"],
        input_dict["Input_Usage"],
        input_dict["Labor"]
    ]

    prediction = model.predict([model_features])[0]

    result =  {
        "username": username,
        "credit_score": prediction[0],
        "Repayment_status": prediction[1],
        "data": input_dict,
        "password": password
    }

    # Firebase: Store the result in Firestore
    doc_ref = db.collection("user_profiles").document(username)
    doc_ref.set(result)


    return result

def load_users():
    users = []
    
    # Query the "user_profiles" collection in Firestore
    users_ref = db.collection("user_profiles")
    docs = users_ref.stream()
    
    for doc in docs:
        # Convert Firestore document to dictionary and add to users list
        users.append(doc.to_dict())
    
    return users

@app.get("/get-user/{username}")
async def get_user(username: str):
    # Load users data from results.json
    users_data = load_users()

    # Search for the user in the data
    for user in users_data:
        if user['username'] == username:
            # Return the user data directly
            return user

    # If user is not found, raise a 404 error
    raise HTTPException(status_code=404, detail="User not found")


@app.get("/get-all-users")
async def get_all_users(order: Literal["asc", "desc"] = "desc"):
    users_data = load_users()

    sorted_users = sorted(
        users_data,
        key=lambda x: x.get("Repayment_status", 0),
        reverse=(order == "desc")
    )

    return sorted_users



@app.put("/update/{username}")
def update_user(username: str, updated_data: dict):
    doc_ref = db.collection("user_profiles").document(username)
    doc = doc_ref.get()

    if not doc.exists:
        raise HTTPException(status_code=404, detail="User not found")

    user_info = doc.to_dict()

    current_data = user_info.get("data", {})
    password = user_info.get("password", "")
    firstname = current_data.get("FirstName", "")
    lastname = current_data.get("LastName", "")

    # Merge updates into current_data
    merged_data = {**current_data, **updated_data}

    # Apply mappings if required
    for key, map_dict in mappings.items():
        if key in merged_data:
            merged_data[key] = map_dict.get(merged_data[key], 0)

    # Prepare input features for model
    feature_order = [
        "Age", "Gender", "Education", "Marital_Status", "Region", "State",
        "Farm_Size", "Crop_Type", "Livestock_Type", "Livestock_Number", "Irrigation",
        "Crop_Cycles", "Technology_Use", "Previous_Loans", "Loan_Amount", "Repayment_Status",
        "Savings_Behavior", "Financial_Access", "Annual_Income", "Extension_Services",
        "Market_Distance", "Yield_Per_Season", "Input_Usage", "Labor"
    ]

    try:
        model_input = [merged_data.get(feat, 0) for feat in feature_order]
        prediction = model.predict([model_input])[0]  # e.g. [credit_score, repayment]
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Prediction failed: {str(e)}")

    updated_record = {
        "username": username,
        "password": password,
        "credit_score": prediction[0],
        "Repayment_status": prediction[1],
        "data": {
            **merged_data,
            "FirstName": firstname,
            "LastName": lastname
        }
    }

    doc_ref.set(updated_record)
    return updated_record

class LoginPayload(BaseModel):
    username: str
    password: str

@app.post("/login")
async def login(payload: LoginPayload):
    users_data = load_users()

    for user in users_data:
        if user['username'] == payload.username:
            if user['password'] == payload.password:
                return user
    return {"error": "Invalid credentials"}

verification_codes = {}

class EmailInput(BaseModel):
    email: str

class CodeInput(BaseModel):
    email: str
    code: str

def generate_code():
    return str(random.randint(100000, 999999))

async def send_email_code(email: str, code: str):
    send_email(email=email, code=code)

@app.post("/send-code")
async def send_code(payload: EmailInput):
    try:
        validated = validate_email(payload.email).email
    except EmailNotValidError as e:
        raise HTTPException(status_code=400, detail=str(e))

    code = generate_code()
    verification_codes[validated] = code
    await send_email_code(validated, code)
    return {"message": f"Code sent to {validated}"}

@app.post("/verify-code")
def verify_code(payload: CodeInput):
    stored = verification_codes.get(payload.email)
    if stored and stored == payload.code:
        verification_codes.pop(payload.email)  # clean up
        return {"message": "Email verified successfully!"}
    raise HTTPException(status_code=400, detail="Invalid code")


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)

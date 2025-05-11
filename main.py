from fastapi import FastAPI
from pydantic import BaseModel
import joblib
import uvicorn
import os
import json
from fastapi.middleware.cors import CORSMiddleware

# Define the User model to match the data structure you want to return



app = FastAPI()

# Add CORS middleware to your app
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],  # Allow your frontend to make requests
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
        "data": input_dict
    }

    # Store in results.json
    results_path = "results.json"
    if os.path.exists(results_path):
        with open(results_path, "r") as f:
            try:
                existing = json.load(f)
            except json.JSONDecodeError:
                existing = []
    else:
        existing = []

    existing.append(result)
    with open(results_path, "w") as f:
        json.dump(existing, f, indent=2)

    return result

def load_users():
    results_path = "results.json"
    if os.path.exists(results_path):
        with open(results_path, "r") as f:
            try:
                return json.load(f)
            except json.JSONDecodeError:
                return []
    else:
        return []

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

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)

📌 Overview

SmartBill AI is an intelligent energy monitoring and billing system that predicts monthly electricity consumption using machine learning and provides accurate bill estimation based on appliance usage.

The system combines ML-based baseline prediction with user-specific appliance usage to generate realistic and personalized electricity bills.

🚀 Features
📊 Predicts monthly energy consumption using ML models
⚡ Estimates appliance-level energy usage (Power × Time)
🔄 Adjusts baseline consumption dynamically
💰 Calculates electricity bill using slab-based rules
🖥️ Interactive UI built with Streamlit
📈 Provides insights into energy usage patterns
🧠 Tech Stack
Frontend: Streamlit
Backend: Python
Machine Learning:
Ridge Regression
Random Forest
XGBoost
Dataset: UCI Household Power Consumption Dataset
Other Libraries: Pandas, NumPy, Scikit-learn
🏗️ Project Architecture
User Input (Appliances + Usage Hours)
            ↓
Appliance Energy Calculation (Power × Time)
            ↓
ML Model → Baseline Consumption Prediction
            ↓
Scaling Factor = Appliance_kWh / Avg Indian Usage (~275 kWh)
            ↓
Adjusted Final Consumption
            ↓
Rule-Based Billing System
            ↓
Final Electricity Bill Output
⚙️ How It Works
1. Baseline Prediction

Machine learning models predict the expected monthly energy consumption based on historical data.

2. Appliance-Based Calculation

User inputs:

Number of appliances
Daily usage hours

Energy is calculated as:

Energy (kWh) = Power (kW) × Time (hours)
3. Adjustment Factor

The predicted baseline is scaled using:

Adjustment Factor = Appliance Energy / 275
4. Final Consumption
Final Consumption = Baseline × Adjustment Factor
5. Bill Calculation

Electricity bill is calculated using slab-based pricing rules.

📂 Project Structure
SmartBill-AI/
│
├── prediction.py        # ML model & prediction logic
├── app.py               # Streamlit UI
├── billing.py           # Slab-based bill calculation
├── dataset/             # UCI dataset
├── models/              # Trained ML models
└── README.md
▶️ Installation & Setup
1. Clone the Repository
git clone https://github.com/your-username/smartbill-ai.git
cd smartbill-ai
2. Install Dependencies
pip install -r requirements.txt
3. Run the Application
streamlit run app.py

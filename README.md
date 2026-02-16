# ExpenseMate


# ExpenseMate 

## How to Run Locally

1. Create virtual environment:
python -m venv venv
source venv/bin/activate  (Mac/Linux)
venv\Scripts\activate     (Windows)

2. Install dependencies:
pip install -r requirements.txt

3. Run:
python app.py

Open browser:
http://127.0.0.1:5000

## Deployment (Render/Heroku)
- Push to GitHub
- Connect repo
- Add environment variable SECRET_KEY
- Deploy (Procfile included)


expensemate/
│
├── instance/              ✅ Correct (Flask DB storage)
│   └── expensemate.db
│
├── static/                ✅ CSS + JS
├── templates/             ✅ Proper separation
      └── base.html
      └── Dashboard.html
      └── login.html
      └── register.html
├── app.py                 ✅ Main entry
├── requirements.txt       ⚠ Must verify versions
└── README.md
Enjoy 🚀




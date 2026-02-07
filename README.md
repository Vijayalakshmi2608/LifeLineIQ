# 🏥 GRASP Hackathon – AI-Assisted Rural Health Triage & Care Navigation

## 🌟 Overview
This project is a **full-stack prototype** that helps rural populations understand the urgency of their health symptoms and guides them to the right level of care.

The system converts user-reported symptoms into a **structured urgency assessment** with:
- Clear reasoning
- Actionable care guidance
- Nearby facility suggestions (prototype data)

It aims to reduce unnecessary hospital visits while ensuring critical cases are not delayed.

---

## 🚨 Problem Statement
Rural healthcare systems face two major challenges:

1. **Overcrowding** due to non-urgent cases.
2. **Delayed treatment** for serious conditions because patients don’t know when care is truly urgent.

People struggle to answer:
- *Is my condition serious?*
- *Where should I go?*
- *Is the nearest facility appropriate for my symptoms?*

---

## 💡 Proposed Solution
An AI-assisted triage and care navigation system that:

- Collects symptoms from users
- Applies intelligent decision logic
- Explains *why* a case is urgent or non-urgent
- Suggests suitable healthcare facilities
- Works in low-resource and rural-friendly UI settings

---

## 🧱 System Architecture

**React Frontend → REST API → Python Backend → SQLite Database**

---

## 🎨 Frontend

### Tech Stack
- React
- JavaScript
- HTML / CSS

### Responsibilities
- Symptom input form
- Urgency result visualization
- Care guidance UI
- Facility listing (prototype data)
- Mobile-friendly & rural-friendly UX

---

## ⚙️ Backend

### Tech Stack
- Python
- FastAPI

### Responsibilities
- Process symptom inputs
- Apply triage rules
- Generate structured urgency reports
- Serve healthcare facility data via APIs

---

## 🗄️ Database

### Technology
- SQLite

### Purpose
- Store healthcare facility details
- Maintain prototype-level resource data
- Support backend decision flow

---

## 🧠 AI / Decision Logic (Prototype)

This version uses **rule-based decision logic** to simulate AI behavior.

### Example Rules
- High fever + long duration + young/elderly → High urgency
- Chest pain / breathing difficulty → Immediate hospital guidance
- Mild symptoms + short duration → Home care or clinic

Each output includes:
✔ Urgency Level  
✔ Explanation  
✔ Recommended Next Step  

> The architecture supports future ML/NLP model integration.

---

## ✨ Key Features

- Symptom-based urgency classification  
- Explainable triage reasoning  
- Clear next-step care guidance  
- Nearby clinic / hospital suggestions  
- Rural-friendly, simple UI  
- Modular & scalable architecture  

---

## 🚀 How to Run Locally

### Prerequisites
- Node.js
- Python 3.x
- Git

---

### 🔧 Backend Setup
```bash
cd backend
pip install -r requirements.txt
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
---

### 🎨 Frontend Setup
```bash
cd frontend
npm install
npm run dev

📁 Repository Structure
/frontend   → React UI
/backend    → FastAPI services
README.md   → Project documentation

🧪 Prototype Scope

✔ Frontend UI implemented
✔ Backend APIs completed
✔ SQLite database integrated
✔ Local execution supported

🔮 Future Enhancements

Machine learning–based symptom analysis

NLP-powered free-text symptom input

GPS & map integration

Doctor availability & appointment scheduling

Multi-language support

Offline-first mode for rural connectivity

🏆 What This Prototype Demonstrates

Clear understanding of healthcare triage challenges

Responsible handling of medical uncertainty

Explainable and defensible decision logic

Scalable full-stack architecture

📜 License

Developed for academic and hackathon evaluation purposes only.

⚠️ Disclaimer: This system is a prototype and not a substitute for professional medical diagnosis.

# GRASP HACKATHON
# AI-Assisted Rural Health Triage & Care Navigation

## Overview
This project is a **full-stack prototype** designed to assist rural users in understanding the urgency of their health conditions and guide them to the appropriate healthcare facilities.  
The system converts user-reported symptoms into a **structured urgency assessment** with clear reasoning and actionable care guidance.

---

## Problem Statement
Rural healthcare systems are often overwhelmed by non-emergency cases, while serious conditions go unnoticed due to delayed decision-making and lack of guidance.

Patients struggle to understand:
- Whether their condition is urgent
- Where they should seek care
- If nearby facilities are suitable for their condition

---

## Proposed Solution
An AI-assisted triage and care navigation system that:
- Collects symptom inputs from users
- Assesses urgency using decision logic
- Explains *why* a condition is urgent or non-urgent
- Suggests suitable nearby healthcare facilities (prototype-level data)

---

## System Architecture

React Frontend | REST API | Python Backend | SQLite Database

---

## Frontend

### Technology Stack
- React
- JavaScript
- HTML / CSS

### Responsibilities
- Symptom input interface
- Urgency result visualization
- Care pathway guidance display
- Healthcare resource listing (prototype)

---

## Backend

### Technology Stack
- Python


### Responsibilities
- Process symptom inputs
- Apply triage decision rules
- Generate structured urgency reports
- Serve healthcare resource data

---

## Database

### Technology
- SQLite

### Purpose
- Store healthcare facility details
- Maintain prototype resource data
- Support backend decision-making flow

---

## AI / Decision Logic (Prototype)
This prototype uses **rule-based decision logic** to simulate AI behavior.

### Example Logic
- Symptom combinations such as fever severity, age, and duration increase urgency score
- High-risk patterns trigger immediate clinic or hospital guidance
- Each output includes a **reasoned explanation**, not just a label

> The architecture supports future integration of ML or NLP models.

---

## Key Features
- Symptom-based urgency classification
- Explainable triage reasoning
- Clear next-step care guidance
- Nearby clinic/hospital suggestions (static prototype data)
- Simple, rural-friendly user interface

---

## How to Run Locally

### Prerequisites
- Node.js
- Python 3.x
- Git

### Backend Setup
```bash
cd backend
pip install -r requirements.txt
uvicorn app.main:app --host 0.0.0.0


### Frontend Setup

cd frontend
npm install
npm run dev



### Repository Structure

/frontend    → React-based user interface
/backend     → Python backend services
README.md




Prototype Scope

Frontend UI completed

Backend APIs implemented

SQLite database integrated

Local execution supported




---

Enhancements

Machine learning–based symptom analysis

Real-time GPS and map integration

Doctor availability and appointment data

Multi-language support

Offline-first functionality for rural areas



---


This prototype demonstrates:

Clear understanding of the healthcare triage problem

Responsible handling of medical uncertainty

Explainable and defensible decision logic

Scalable and modular system architecture



---

License

This project is developed for academic and hackathon evaluation purposes only.

---

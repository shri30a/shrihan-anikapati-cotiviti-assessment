# Clinical Report AI Assistant – Proof of Concept

## Overview

This Proof of Concept (POC) was developed as part of the Cotiviti Intern Assessment to demonstrate how generative AI can assist healthcare professionals by streamlining clinical documentation review.

The application enables users to upload a clinical report and automatically generates structured insights, including patient summaries, key clinical information, and documentation quality feedback. The goal is to demonstrate how AI can reduce the time required to review lengthy medical documentation while improving consistency and usability.

---

## Features

* AI-generated patient summary
* Medical condition extraction
* Medication and allergy identification
* Laboratory and imaging result extraction
* Documentation issue detection
* Interactive Streamlit dashboard
* Modern Cotiviti-inspired user interface

---

## Technology Stack

* Python
* Streamlit
* Google Gemini API
* PyPDF
* Pandas
* Regular Expressions (Regex)

---

## Project Files

```text
app.py               Main Streamlit application
requirements.txt     Python dependencies
sample_demo.pdf      Synthetic clinical report for demonstration
README.md            Project documentation
```

---

## Running the Application

### 1. Install the required packages

```bash
pip install -r requirements.txt
```

### 2. Configure your Google Gemini API Key

Before launching the application, configure your own Google Gemini API key as an environment variable or through your preferred secure configuration method.

> **Note:** API keys are intentionally excluded from this repository for security reasons.

### 3. Launch the application

```bash
streamlit run app.py
```

---

## Demonstration

Use the included **sample_demo.pdf** to explore the application's capabilities, including:

* AI-generated patient summaries
* Clinical information extraction
* Medication and allergy identification
* Laboratory and imaging result extraction
* Documentation quality review
* Interactive dashboard visualization

---

## Disclaimer

This application was developed solely for demonstration purposes as part of the Cotiviti Intern Assessment.

The included clinical report contains **synthetic demonstration data only**. No protected health information (PHI) or real patient information is included.

This proof of concept is intended exclusively for educational and demonstration purposes and is **not** intended for clinical use or medical decision-making.

---

## Author

**Shrihan Anikapati**

Electrical and Computer Engineering (Honors) & Mathematics
The University of Texas at Austin

Interests: Artificial Intelligence, Machine Learning, Healthcare Technology, and Software Engineering.


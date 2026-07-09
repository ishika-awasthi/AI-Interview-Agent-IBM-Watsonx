##🎓 AI Interview Trainer

![Python](https://img.shields.io/badge/Python-3.11-blue)
![Streamlit](https://img.shields.io/badge/Streamlit-App-red)
![IBM watsonx.ai](https://img.shields.io/badge/IBM-watsonx.ai-blue)
![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)

An AI-powered Interview Preparation Assistant built using **IBM Granite** on **IBM watsonx.ai**. The application generates interview questions, evaluates candidate responses, provides detailed AI-driven feedback, and generates a comprehensive interview performance report.

Developed as part of the **IBM SkillsBuild AICTE Internship Program** in collaboration with **Edunet Foundation**.

---

## 📌 Features

- 🤖 AI-generated interview questions
- 📚 Multiple interview domains
  - Python
  - Machine Learning
  - HR & Behavioural
  - Cloud & DevOps
  - Data Structures & Algorithms
- 📊 Instant AI evaluation
- ✅ Detailed feedback including:
  - Overall Score
  - Technical Accuracy
  - Clarity
  - Completeness
  - Strengths
  - Weaknesses
  - Ideal Answer
- 📈 Interactive performance dashboard
- 📄 Downloadable interview report (JSON)
- 🔄 Multiple interview sessions
- 🎨 Modern Streamlit-based responsive UI

---

## 🛠️ Technology Stack

- Python
- Streamlit
- IBM watsonx.ai
- IBM Granite Foundation Model
- IBM WatsonX AI SDK
- python-dotenv

---

## 📂 Project Structure

```
AI-Interview-Trainer/
│
├── app.py                      # Streamlit application
├── main.py                     # CLI application
├── requirements.txt
├── .env.example
├── README.md
├── LICENSE
│
├── models/
│   └── watsonx_client.py
│
├── prompts/
│   ├── interview_prompt.py
│   ├── question_prompt.txt
│   ├── evaluation_prompt.txt
│   └── summary_prompt.txt
│
├── report/
│   └── history_manager.py
│
├── utils/
│   └── text_utils.py
│
└── interview_history/
```

---

## ⚙️ Installation

### 1. Clone the repository

```bash
git clone <repository-url>
cd AI-Interview-Trainer
```

### 2. Create a virtual environment

Windows

```bash
python -m venv venv
venv\Scripts\activate
```

Linux / macOS

```bash
python3 -m venv venv
source venv/bin/activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

---

## 🔑 Environment Variables

Create a `.env` file in the project root.

```env
WATSONX_API_KEY=YOUR_API_KEY
WATSONX_PROJECT_ID=YOUR_PROJECT_ID
WATSONX_URL=https://us-south.ml.cloud.ibm.com
MODEL_ID=ibm/granite-4-h-small
```

---

## ▶️ Running the Application

### Streamlit Interface

```bash
streamlit run app.py
```

### Command Line Version

```bash
python main.py
```

---

## 📖 How It Works

1. Select an interview domain.
2. The IBM Granite model generates an interview question.
3. The candidate submits an answer.
4. IBM Granite evaluates the response.
5. AI provides detailed feedback and scoring.
6. The process repeats for five interview questions.
7. A final performance summary and downloadable report are generated.

---

## 📊 Evaluation Metrics

Each answer is evaluated on:

- Overall Score
- Technical Accuracy
- Clarity
- Completeness

Additionally, the AI provides:

- Strengths
- Weaknesses
- Ideal Answer

---

## 📸 Application Screenshots

### 🏠 Home Page
Select an interview domain and start a 5-question AI-powered interview session.

![Home Page](screenshots/home%20page.png)

---

### 💬 Interview Question
Answer AI-generated interview questions in real time.

![Interview Question](screenshots/page%202.png)

---

### 📊 AI Evaluation & Feedback
Receive instant AI-generated scores, strengths, weaknesses, and an ideal answer for improvement.

![AI Feedback](screenshots/page%203.png)

---

### 📈 Final Dashboard
View your overall interview grade, average scores across evaluation dimensions, and session summary.

![Final Dashboard](screenshots/page%204.png)

---

### 📝 AI Session Report
Review a comprehensive AI-generated report including:

- Performance Summary
- Technical Strengths
- Areas for Improvement
- Learning Roadmap
- Recommended Topics

![Session Report](screenshots/page%205.png)

---

## 🚀 Future Enhancements

- 🎤 Voice-based interview mode
- 📄 Resume-based personalized interview generation
- 🎯 Difficulty level selection (Beginner, Intermediate, Advanced)
- 💻 Support for additional technical domains
- 📑 PDF report generation
- 👤 User authentication and profile management
- 📚 Interview history dashboard
- 🎙️ Speech-to-text integration
- 📈 Performance analytics across multiple interview sessions

---

## 👩‍💻 Developer

**Ishika Awasthi**

B.Tech Computer Science & Engineering  
COER University, Roorkee


---

##  Acknowledgements

This project was developed as part of the **IBM SkillsBuild AICTE Internship Program** in collaboration with **Edunet Foundation**.

Special thanks to:

- IBM SkillsBuild
- IBM watsonx.ai
- IBM Granite Foundation Models
- Edunet Foundation

for providing the learning resources, cloud platform, and AI technologies used in this project.

---

## 📜 License

This project is licensed under the **MIT License**.

Copyright © 2026 **Ishika Awasthi**

Developed for educational purposes as part of the **IBM SkillsBuild AICTE Internship Program**.

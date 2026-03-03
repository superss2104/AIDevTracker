# AI-Dev-Tracker
### AI-Assisted Software Development Traceability Tool

---

## 📌 Project Overview

AI-Dev-Tracker is a CLI-based tool designed to track, analyze, and measure the impact of AI-assisted development in software projects.

As developers increasingly rely on AI tools (e.g., ChatGPT, Claude), there is no systematic way to:

- Track prompt history
- Link AI responses to code changes
- Measure AI contribution to final software
- Identify areas where developers struggled

This tool provides a structured solution to record, analyze, and report AI-assisted development activity.

---

## 🎯 Problem Statement

Modern software development increasingly integrates AI-generated code. However, there is no standardized mechanism to:

- Maintain prompt history
- Link AI interactions to version control
- Identify which parts of code were AI-generated
- Analyze developer struggle through AI usage patterns

AI-Dev-Tracker addresses this by creating a Git-linked AI interaction logging and analysis system.

---

## 🚀 Key Features

- CLI-based prompt logging
- AI response tracking
- Git commit hash integration
- File-wise prompt mapping
- Similarity-based relevance detection
- AI contribution reporting
- Offline mock AI support (for stable testing)

---

## 🏗️ System Architecture
<img width="1372" height="479" alt="architecture_UML" src="https://github.com/user-attachments/assets/edcbb4a6-e8aa-4694-9a26-22e3d74ea95f" />


---

## 🔄 Workflow Chart
<img width="733" height="782" alt="workflow" src="https://github.com/user-attachments/assets/419aa2ab-6d49-429c-ab5b-6e8f835b93bd" />


---

## 📊 AI Contribution Evaluation Methodology

AI contribution is measured using the following metrics:

1. Prompt Count per File  
   - Number of AI prompts linked to a specific file.

2. Git Commit Linkage  
   - Each prompt is associated with a commit hash.

3. Similarity-Based Relevance Detection  
   - Text similarity between AI response and final file content.
   - Uses SequenceMatcher ratio.
   - Default threshold = 0.4

4. Relevance Classification  
   - If similarity > 0.4 → Marked as AI-contributed.
   - Otherwise → Marked as non-contributing interaction.

These metrics help identify:
- AI-dependent modules
- Developer struggle areas
- AI usage intensity across project timeline

---

## ⚠️ Limitations

- Uses text-based similarity (not semantic embeddings)
- Mock AI engine used for offline testing
- Similarity threshold may require tuning
- No deep architectural inference implemented

---

## 🔮 Future Enhancements

- Embedding-based similarity scoring
- Multi-LLM support
- Web dashboard visualization
- Developer struggle heatmap
- Architectural drift detection
- Export reports to CSV/PDF

---

## 👥 Team Members

- Shivam – System Architecture & Core Implementation
- Suhail – API Testing & Database Design
- Sreeja – Documentation, System Architecture & workflow chart
- Anil – Testing & CLI Validation
- Harsith – Research & Architectural Drift Study

---

## 📚 Academic Purpose

This project is developed as part of a Software Engineering Lab to study:

- AI-assisted development traceability
- Version control integration
- AI contribution quantification
- Software maintainability analysis

---

## 📜 License

Academic Project – Educational Use Only

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

- **Multi-LLM support** — works with any OpenAI-compatible provider (Gemini, OpenAI, Groq, Mistral, etc.)
- **Interactive model switching** — select a provider at startup or switch anytime via CLI
- CLI-based prompt logging
- AI response tracking
- Session-based project management
- Git commit hash integration
- File-wise prompt mapping
- Similarity-based relevance detection
- AI contribution reporting
- Struggle detection (rapid-prompt, sustained, escalating, long-session)

---

## ⚙️ Setup

1. Clone the repo and install dependencies:
   ```bash
   pip install openai python-dotenv
   ```

2. On first run, you'll be prompted to select your LLM provider:
   ```
   Select your LLM provider:
     1. Gemini
     2. OpenAI
     3. Groq
     4. Other (custom base URL)
   ```

3. Or configure manually in `.env`:
   ```env
   LLM_API_KEY=your_api_key_here
   LLM_BASE_URL=https://generativelanguage.googleapis.com/v1beta/openai/
   LLM_MODEL=gemini-2.5-flash
   ```

---

## 🔧 CLI Commands

```bash
python main.py ask "prompt" [file.py]         # Ask the AI
python main.py analyze [file.py]               # Run analysis
python main.py report                          # Generate report
python main.py visualize                       # Show visual summary
python main.py export [output.csv]             # Export to CSV
python main.py session <new|list|use> [args]   # Manage sessions
python main.py model                           # Switch LLM (interactive)
python main.py model <KEY> --base-url <URL> --model <MODEL>  # Switch LLM (direct)
```


---

## 🏗️ System Architecture



![WhatsApp Image 2026-03-17 at 8 34 41 AM](https://github.com/user-attachments/assets/4ecb67f4-06d6-4578-864d-d555f8ed498a)

---

## 🔄 Workflow Chart

![WhatsApp Image 2026-03-14 at 1 38 14 PM](https://github.com/user-attachments/assets/734ade65-a637-4657-9090-1daf89aeaa31)

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
- Web dashboard visualization
- Developer struggle heatmap
- Architectural drift detection
- Export reports to PDF

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

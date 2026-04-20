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
- Maintain structured, goal-driven development sessions

This tool provides a structured solution to record, analyze, and report AI-assisted development activity.

---

## 🎯 Problem Statement

Modern software development increasingly integrates AI-generated code. However, there is no standardized mechanism to:

- Maintain prompt history
- Link AI interactions to version control
- Identify which parts of code were AI-generated
- Analyze developer struggle through AI usage patterns
- Ensure session coherence when developers ask unrelated questions mid-session

AI-Dev-Tracker addresses this by creating a Git-linked AI interaction logging and analysis system with structured session flow enforcement.

---

## 🚀 Key Features

- **Multi-LLM support** — works with any OpenAI-compatible provider (Gemini, OpenAI, Groq, Mistral, etc.)
- **Interactive model switching** — select a provider at startup or switch anytime via CLI
- **Structured session flow** — goal-driven sessions with relevance enforcement
  - **Session goals** — attach a purpose/topic to each session
  - **Soft warning** — warns when a prompt appears off-topic, asks to confirm
  - **Guard mode** — hard-blocks off-topic prompts entirely (opt-in)
  - **AI system prompt scoping** — the AI is instructed to stay on-topic and redirect unrelated questions
  - **Session summary** — view a structured overview of the current session at any time
- CLI-based prompt logging
- AI response tracking with **rich markdown rendering** in the terminal
- Session-based project management
- Git commit hash integration
- File-wise prompt mapping
- Multi-source relevance detection (keyword overlap against first prompt, session goal, and recent conversation)
- AI contribution reporting
- Struggle detection (rapid-prompt, sustained, escalating, long-session)


---

## ⚙️ Setup

1. Clone the repo and install dependencies:
   ```bash
   pip install openai python-dotenv rich
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
   RELEVANCE_THRESHOLD=0.4
   ```

---

## 🔧 CLI Commands

### Core Commands

```bash
python main.py ask "prompt" [file.py]         # Ask the AI (with optional file context)
python main.py analyze [file.py]               # Run analysis (repo-wide or per-file)
python main.py report                          # Generate detailed AI contribution report
python main.py visualize                       # Show visual summary
python main.py export [output.csv]             # Export interactions to CSV
```

### Session Management

```bash
python main.py session new "Project Name" [--goal "Session goal"]   # Create a new session
python main.py session list                                         # List all sessions
python main.py session use <id>                                     # Switch active session
python main.py session guard <on|off>                               # Toggle hard-block guard mode
python main.py session summary                                      # Show active session overview
```

### Model Configuration

```bash
python main.py model                                                # Switch LLM (interactive)
python main.py model <KEY> --base-url <URL> --model <MODEL>         # Switch LLM (direct)
```

### Global Flags

```bash
python main.py --threshold <0.0-1.0> <command>                     # Override relevance threshold
```

---

## 🛡️ Structured Session Flow

Sessions can be created with a **goal** that defines the session's purpose. This enables:

1. **AI System Prompt Scoping** — the AI is primed to stay focused on the session goal and redirect off-topic questions.
2. **Pre-flight Relevance Check** — before each AI call, the prompt is compared against three context sources using keyword overlap:
   - First prompt for the file (topical anchor)
   - Session goal (overall scope)
   - Most recent prompt + response (conversational continuity)
   - The **max** of all scores is used — if relevant to *any* source, the prompt passes.
3. **Soft Warning** (default) — if the prompt scores below the threshold, the developer is warned and asked `Proceed anyway? [y/N]`.
4. **Guard Mode** (opt-in) — when enabled via `session guard on`, off-topic prompts are hard-blocked with no AI call made.

```
Developer: python main.py ask "..." file.py
              │
              ▼
     Session active AND file has a prior prompt?
              │
        Yes   ├── max(keyword_overlap scores) < threshold?
              │         │
              │    Yes   ├── guard_mode ON  → 🚫 HARD BLOCK
              │          └── guard_mode OFF → ⚠  Soft warn → y/N
              │    No    └── Proceed
              ▼
     AI responds (system prompt scoped to session goal)
              │
              ▼
     Relevance scored → Interaction saved to DB
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

1. **Prompt Count per File**
   - Number of AI prompts linked to a specific file.

2. **Git Commit Linkage**
   - Each prompt is associated with a commit hash.

3. **Hybrid Relevance Detection**
   - Two methods are used and the **higher** score is taken:
     - `SequenceMatcher` — catches verbatim text/code reuse
     - `Keyword Overlap` — catches topical relevance (shared terms)
   - Default threshold = 0.4 (configurable via `.env` or `--threshold` flag)

4. **Relevance Classification**
   - If score ≥ threshold → Marked as AI-contributed.
   - Otherwise → Marked as non-contributing interaction.

5. **Struggle Detection**
   - Rapid-prompt struggle (< 5 min between prompts)
   - Sustained struggle (3+ prompts within a 30-min window)
   - Escalating dependency (prompt frequency accelerating over time)
   - Long session (continuous AI usage over 2+ hours on a file)

These metrics help identify:
- AI-dependent modules
- Developer struggle areas
- AI usage intensity across project timeline

---

## 📋 Metadata Captured

Per-interaction: `prompt`, `response`, `file_path`, `commit_hash`, `timestamp`, `prompt_length`, `response_length`, `model_used`, `response_time`, `relevance`, `session_id`

Per-session: `project_name`, `created_at`, `goal`, `guard_mode`

See [metadata.md](metadata.md) for the full reference.

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

# Lab: LLM/AI Workflows with LangChain

Build multi-step AI workflows (chains) using LangChain. You'll learn how LLMs can be composed into pipelines where the output of one step feeds the next — and how to handle errors gracefully when things go wrong.

**Time:** ~1.5 hours
**Environment:** Google Colab (recommended for Python) or GitHub Codespaces

---

## Getting Started

### Option A: Google Colab (Recommended for the Python notebook)

Click the badge below to open the Python notebook directly in Colab — no setup required:

[![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/RPI-WS-spring-2026/Agents1/blob/main/python-workflow/workflow_example.ipynb)

**Setting your API key in Colab:**
1. Get a free API key at [console.groq.com](https://console.groq.com)
2. Click the **key icon** (🔑) in the Colab left sidebar
3. Add a new secret named `GROQ_API_KEY` with your Groq API key as the value
4. Toggle **"Notebook access"** on

> **Note:** For the Node.js exercises (Parts 2a and 2b), use Codespaces (Option B below).

### Option B: GitHub Codespaces (Node.js exercises)

The Codespace is a lightweight Node.js environment — it should start in under a minute.

1. Accept the GitHub Classroom assignment using the link provided by your instructor
2. Go to **your** assignment repository
3. Click the green **Code** button, then the **Codespaces** tab
4. Click **Create codespace on main**

When it opens, the Node.js dependencies install automatically. Set your API key:

```bash
export GROQ_API_KEY="your-key-here"
```

---

## Background: What Is a Workflow/Chain?

An AI **workflow** (or **chain**) is a sequence of steps where each step transforms data, calls an LLM, or performs some action. The output of one step becomes the input to the next.

**Example workflow — Blog Post Generator:**
```
Topic → [Generate Outline] → [Write Draft] → [Summarize] → Final Output
```

Each arrow represents a step that could be an LLM call, a data transformation, or an API call. LangChain provides the glue to connect these steps together.

### Why Workflows Matter

- **Decomposition:** Complex tasks are broken into manageable steps
- **Reusability:** Individual steps can be reused across different workflows
- **Debuggability:** You can inspect the output at each stage
- **Error handling:** Failures at one step can be caught and handled without crashing the whole pipeline

### Error Handling in AI Workflows

LLM workflows introduce unique error scenarios that don't exist in traditional programming:

| Error Type | Description | Handling Strategy |
|---|---|---|
| **API Errors** | Rate limits, timeouts, authentication failures | Retry with exponential backoff; use fallback models |
| **Malformed Output** | LLM returns text that doesn't match expected format (e.g., invalid JSON) | Output parsers with retry; structured output prompts |
| **Token Limits** | Input or output exceeds the model's context window | Truncate input; split into chunks; use models with larger context |
| **Hallucination / Bad Content** | LLM generates incorrect or inappropriate content | Validation steps; guardrails; human-in-the-loop review |
| **Chain Propagation** | An error in step 2 produces garbage input for step 3 | Validate intermediate outputs; use fallback chains |

**Key principle:** Never trust raw LLM output in a production workflow. Always validate, parse, and handle failures at each step.

---

## Part 1: Python Workflow (Jupyter Notebook) (~30 min)

### Setup

```bash
cd python-workflow
pip install -r requirements.txt
```

### Run the Notebook

Open `workflow_example.ipynb` in your Codespace. This notebook walks you through:

1. **Setting up** LangChain with an LLM provider
2. **Building a simple chain** — a prompt template connected to an LLM
3. **Creating a multi-step workflow** — topic → outline → draft → summary
4. **Error handling** — catching API errors, handling malformed output, using fallbacks
5. **Structured output** — getting the LLM to return valid JSON

Work through each cell, reading the explanations and running the code. Modify the prompts to see how changes affect the output.

> **API Key:** This lab uses **Groq API** (free). Get a key at [console.groq.com](https://console.groq.com), then set it:
> ```bash
> export GROQ_API_KEY="your-key-here"
> ```
> On Colab, add it as a Secret named `GROQ_API_KEY` (see setup instructions above).

---

## Part 2: Node.js Workflows (JavaScript) (~30 min)

Two Node.js examples are provided in separate directories, each showing a different approach to AI workflows.

### 2a: Basic Workflow (`node-workflow-basic/`)

A content generation pipeline that takes a topic and produces a structured blog post.

```bash
cd node-workflow-basic
npm install
node workflow.js
```

This example demonstrates:
- Sequential chain execution (output of step N feeds step N+1)
- Prompt templates with variable substitution
- Basic error handling with try/catch
- Retry logic for transient API failures

### 2b: Advanced Workflow (`node-workflow-advanced/`)

A research assistant that takes a question, generates search queries, synthesizes information, and produces a cited answer — with branching logic and parallel execution.

```bash
cd node-workflow-advanced
npm install
node workflow.js
```

This example demonstrates:
- **Parallel chain execution** — running multiple LLM calls concurrently
- **Conditional branching** — different paths based on intermediate results
- **Structured output parsing** — forcing JSON output and validating it
- **Fallback chains** — switching to a simpler model if the primary fails
- **Custom error classes** — distinguishing between retryable and fatal errors

---

## Part 3: Your Novel Workflow (~30 min)

Now it's your turn. Design and implement **your own original workflow** using LangChain in either Python or JavaScript (your choice).

### Requirements

1. Your workflow must have **at least 3 steps** (LLM calls, transformations, or API calls)
2. It must include **error handling** (at minimum: try/catch around LLM calls and validation of at least one intermediate output)
3. It should do something **novel** — not a copy of the examples provided. Think about what kind of multi-step AI task would be useful as part of a broader web application.

### Ideas to Get You Started

- **Code Review Pipeline:** Code snippet → identify issues → suggest fixes → generate improved version
- **Recipe Generator:** Ingredients list → suggest recipes → pick one → generate full recipe with nutritional info
- **Email Composer:** Key points + tone → draft email → check for issues → final version
- **Study Guide Creator:** Lecture notes → extract key concepts → generate practice questions → create summary
- **Product Description Writer:** Product specs → generate descriptions for different audiences → A/B test variants
- **Accessibility Checker:** HTML content → identify accessibility issues → suggest fixes → generate improved HTML
- **Meeting Summarizer:** Raw notes → extract action items → prioritize → generate follow-up email
- **Data Pipeline Describer:** SQL schema → generate documentation → create sample queries → explain relationships

### Deliverable: 1-Slide Summary

Create a single slide (as `slide.md`, `slide.html`, or a PDF/image) that answers:

1. **What does your workflow do?** (1-2 sentences)
2. **What are the steps?** (a simple diagram or numbered list)
3. **How does it fit into a broader application?** (what web app would use this workflow?)
4. **What errors can occur and how do you handle them?**

Place your slide file and your workflow code in a new directory called `my-workflow/`.

---

## Error Handling Deep Dive

Before building your own workflow, study these patterns:

### Pattern 1: Retry with Backoff

```javascript
async function callWithRetry(fn, maxRetries = 3) {
  for (let attempt = 1; attempt <= maxRetries; attempt++) {
    try {
      return await fn();
    } catch (error) {
      if (attempt === maxRetries) throw error;
      if (error.status === 429 || error.status >= 500) {
        // Retryable: rate limit or server error
        const delay = Math.pow(2, attempt) * 1000;
        console.log(`Attempt ${attempt} failed, retrying in ${delay}ms...`);
        await new Promise(r => setTimeout(r, delay));
      } else {
        // Non-retryable: bad request, auth error, etc.
        throw error;
      }
    }
  }
}
```

### Pattern 2: Output Validation

```python
import json

def validate_json_output(llm_output, required_keys):
    """Validate that LLM output is valid JSON with required keys."""
    try:
        parsed = json.loads(llm_output)
    except json.JSONDecodeError:
        raise ValueError(f"LLM returned invalid JSON: {llm_output[:100]}...")

    missing = [k for k in required_keys if k not in parsed]
    if missing:
        raise ValueError(f"Missing required keys: {missing}")

    return parsed
```

### Pattern 3: Fallback Chain

```javascript
async function withFallback(primaryFn, fallbackFn) {
  try {
    return await primaryFn();
  } catch (error) {
    console.warn(`Primary failed: ${error.message}. Using fallback.`);
    return await fallbackFn();
  }
}
```

---

## Submitting Your Work

```bash
git add python-workflow/ node-workflow-basic/ node-workflow-advanced/ my-workflow/
git commit -m "Complete LangChain AI workflows lab"
git push
```

Make sure your `my-workflow/` directory contains:
- Your workflow code (`.py`, `.js`, or `.ipynb`)
- Your 1-slide summary (`slide.md`, `slide.html`, or image/PDF)

---

## Discussion Questions

1. **When should you use a multi-step workflow vs. a single prompt?** What are the trade-offs in cost, latency, and quality?

2. **How do you decide what to retry vs. what to fail?** A rate limit is clearly retryable, but what about a hallucinated response?

3. **What are the security implications of chaining LLM outputs?** Could a malicious input in step 1 cause harmful behavior in step 3? (Look up "prompt injection" if you're not familiar.)

4. **How would you test an AI workflow?** Traditional unit tests expect deterministic outputs — LLMs are non-deterministic. What strategies could you use?

5. **Where does error handling belong in a workflow — at each step, at the top level, or both?** What are the trade-offs?

---

## Codespaces Tips

- **Stopping your Codespace:** Auto-stops after 30 minutes of inactivity. Manually stop at [github.com/codespaces](https://github.com/codespaces).
- **Multiple terminals:** Click `+` in the terminal panel. You may want separate terminals for Python and Node.js.
- **Environment variables:** Set your API key once per terminal session with `export GROQ_API_KEY="..."`, or create a `.env` file with `GROQ_API_KEY=your-key` (but **never commit it**).

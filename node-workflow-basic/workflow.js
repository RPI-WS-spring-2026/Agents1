/**
 * Basic LangChain.js Workflow: Content Generation Pipeline
 *
 * This script demonstrates a sequential 3-step workflow:
 *   Topic → [Generate Outline] → [Write Draft] → [Create Summary]
 *
 * Key concepts:
 *   - Prompt templates with variable substitution
 *   - Sequential chain execution (pipe operator)
 *   - Error handling with retry logic
 */

import "dotenv/config";
import { ChatGroq } from "@langchain/groq";
import { ChatPromptTemplate } from "@langchain/core/prompts";
import { StringOutputParser } from "@langchain/core/output_parsers";
import { RunnableLambda } from "@langchain/core/runnables";

// --- Configuration ---
// Uses Groq API (free, ultra-fast inference) — get a key at https://console.groq.com

if (!process.env.GROQ_API_KEY) {
  console.error("ERROR: GROQ_API_KEY is not set.");
  console.error("Get a free key at https://console.groq.com");
  console.error('Set it with: export GROQ_API_KEY="your-key-here"');
  console.error("Or create a .env file with: GROQ_API_KEY=your-key-here");
  process.exit(1);
}

const llm = new ChatGroq({
  model: "llama-3.3-70b-versatile",
  temperature: 0.7,
  apiKey: process.env.GROQ_API_KEY,
});
const outputParser = new StringOutputParser();

// --- Step 1: Generate Outline ---

const outlinePrompt = ChatPromptTemplate.fromTemplate(
  `Create a brief outline for a blog post about: {topic}

The outline should have 3-4 main sections with 2-3 bullet points each.
Format it as a numbered list.`
);

const outlineChain = outlinePrompt.pipe(llm).pipe(outputParser);

// --- Step 2: Write Draft ---

const draftPrompt = ChatPromptTemplate.fromTemplate(
  `Write a short blog post (about 300 words) based on this outline:

{outline}

Make it engaging and informative. Use a conversational tone.`
);

const draftChain = draftPrompt.pipe(llm).pipe(outputParser);

// --- Step 3: Summarize ---

const summaryPrompt = ChatPromptTemplate.fromTemplate(
  `Summarize this blog post in 2-3 sentences:

{draft}`
);

const summaryChain = summaryPrompt.pipe(llm).pipe(outputParser);

// --- Error Handling: Retry with Exponential Backoff ---

async function callWithRetry(chain, inputs, maxRetries = 3) {
  for (let attempt = 1; attempt <= maxRetries; attempt++) {
    try {
      return await chain.invoke(inputs);
    } catch (error) {
      const message = error.message || String(error);
      const isRetryable =
        message.includes("429") ||
        message.includes("500") ||
        message.toLowerCase().includes("timeout");

      if (isRetryable && attempt < maxRetries) {
        const delay = Math.pow(2, attempt) * 1000;
        console.log(
          `  Attempt ${attempt} failed: ${message.slice(0, 60)}...`
        );
        console.log(`  Retrying in ${delay / 1000}s...`);
        await new Promise((r) => setTimeout(r, delay));
      } else {
        throw error;
      }
    }
  }
}

// --- Run the Workflow ---

async function runWorkflow(topic) {
  console.log("=".repeat(60));
  console.log(`Content Generation Workflow`);
  console.log(`Topic: "${topic}"`);
  console.log("=".repeat(60));

  // Step 1
  console.log("\nSTEP 1: Generating outline...");
  let outline;
  try {
    outline = await callWithRetry(outlineChain, { topic });
    console.log(outline);
  } catch (error) {
    console.error(`FATAL: Outline generation failed: ${error.message}`);
    console.error("Cannot continue without an outline.");
    return;
  }

  // Step 2
  console.log("\n" + "-".repeat(60));
  console.log("STEP 2: Writing draft...");
  let draft;
  try {
    // Validate intermediate output before passing to next step
    if (outline.trim().length < 50) {
      throw new Error(
        "Outline is too short — LLM may have returned incomplete output."
      );
    }
    draft = await callWithRetry(draftChain, { outline });
    console.log(draft);
  } catch (error) {
    console.error(`FATAL: Draft generation failed: ${error.message}`);
    return;
  }

  // Step 3
  console.log("\n" + "-".repeat(60));
  console.log("STEP 3: Creating summary...");
  try {
    const summary = await callWithRetry(summaryChain, { draft });
    console.log(summary);
  } catch (error) {
    // Summary is non-critical — we still have the draft
    console.warn(`WARNING: Summary failed (${error.message}). Skipping.`);
  }

  console.log("\n" + "=".repeat(60));
  console.log("Workflow complete!");
}

// --- Bonus: Composed Single Chain ---

async function runComposedWorkflow(topic) {
  console.log("\n" + "=".repeat(60));
  console.log("Running as a single composed chain...");
  console.log("=".repeat(60));

  // Compose all steps into one chain using the pipe operator
  const fullWorkflow = outlineChain
    .pipe(new RunnableLambda({ func: (outline) => ({ outline }) }))
    .pipe(draftChain)
    .pipe(new RunnableLambda({ func: (draft) => ({ draft }) }))
    .pipe(summaryChain);

  try {
    const summary = await fullWorkflow.invoke({ topic });
    console.log("\nFinal summary:");
    console.log(summary);
  } catch (error) {
    console.error(`Workflow failed: ${error.message}`);
  }
}

// --- Main ---

const topic = process.argv[2] || "how AI is changing web development";

await runWorkflow(topic);
await runComposedWorkflow(topic);

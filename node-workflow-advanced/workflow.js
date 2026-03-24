/**
 * Advanced LangChain.js Workflow: Research Assistant
 *
 * A multi-step workflow with parallel execution, conditional branching,
 * structured output parsing, fallbacks, and custom error handling.
 *
 * Workflow:
 *   Question → [Classify Complexity] →
 *     Simple:  [Direct Answer]
 *     Complex: [Generate Sub-Questions] → [Answer Each in Parallel] → [Synthesize]
 *   → [Format Final Output as JSON]
 */

import "dotenv/config";
import { ChatOpenAI } from "@langchain/openai";
import { ChatPromptTemplate } from "@langchain/core/prompts";
import { StringOutputParser } from "@langchain/core/output_parsers";

// --- Configuration ---
// Uses xAI's Grok API (free) — get a key at https://console.x.ai

if (!process.env.XAI_API_KEY) {
  console.error("ERROR: XAI_API_KEY is not set.");
  console.error("Get a free key at https://console.x.ai");
  console.error('Set it with: export XAI_API_KEY="your-key-here"');
  process.exit(1);
}

const llm = new ChatOpenAI({
  model: "grok-3-mini-fast",
  temperature: 0.7,
  configuration: {
    baseURL: "https://api.x.ai/v1",
    apiKey: process.env.XAI_API_KEY,
  },
});
const outputParser = new StringOutputParser();

// --- Custom Error Classes ---
// Distinguishing error types helps decide whether to retry, fallback, or abort.

class RetryableError extends Error {
  constructor(message, attempt) {
    super(message);
    this.name = "RetryableError";
    this.attempt = attempt;
  }
}

class ValidationError extends Error {
  constructor(message, rawOutput) {
    super(message);
    this.name = "ValidationError";
    this.rawOutput = rawOutput;
  }
}

// --- Utility: Retry with Backoff ---

async function callWithRetry(fn, maxRetries = 3) {
  for (let attempt = 1; attempt <= maxRetries; attempt++) {
    try {
      return await fn();
    } catch (error) {
      const msg = error.message || String(error);
      const isRetryable =
        msg.includes("429") ||
        msg.includes("500") ||
        msg.toLowerCase().includes("timeout") ||
        msg.toLowerCase().includes("econnreset");

      if (isRetryable && attempt < maxRetries) {
        const delay = Math.pow(2, attempt) * 1000;
        console.log(`    Retry ${attempt}/${maxRetries} in ${delay / 1000}s...`);
        await new Promise((r) => setTimeout(r, delay));
      } else {
        throw new RetryableError(
          `Failed after ${attempt} attempt(s): ${msg}`,
          attempt
        );
      }
    }
  }
}

// --- Utility: Parse and Validate JSON from LLM ---

function parseJsonOutput(rawOutput, requiredKeys = []) {
  let text = rawOutput.trim();

  // Extract JSON from markdown code fences if present
  const jsonMatch = text.match(/```(?:json)?\s*([\s\S]*?)```/);
  if (jsonMatch) {
    text = jsonMatch[1].trim();
  }

  let parsed;
  try {
    parsed = JSON.parse(text);
  } catch {
    throw new ValidationError(
      `Invalid JSON from LLM: ${text.slice(0, 100)}...`,
      rawOutput
    );
  }

  const missing = requiredKeys.filter((k) => !(k in parsed));
  if (missing.length > 0) {
    throw new ValidationError(
      `Missing required keys: ${missing.join(", ")}`,
      rawOutput
    );
  }

  return parsed;
}

// --- Utility: Fallback Wrapper ---

async function withFallback(primaryFn, fallbackFn, label = "operation") {
  try {
    return await primaryFn();
  } catch (error) {
    console.warn(`  [${label}] Primary failed: ${error.message}`);
    console.warn(`  [${label}] Trying fallback...`);
    return await fallbackFn();
  }
}

// --- Step 1: Classify Question Complexity ---

const classifyPrompt = ChatPromptTemplate.fromTemplate(
  `Classify this question as either "simple" or "complex".

A "simple" question can be answered directly in a few sentences.
A "complex" question requires breaking down into sub-questions.

Question: {question}

Respond with ONLY the word "simple" or "complex", nothing else.`
);

const classifyChain = classifyPrompt.pipe(llm).pipe(outputParser);

async function classifyQuestion(question) {
  const result = await callWithRetry(() =>
    classifyChain.invoke({ question })
  );

  const classification = result.trim().toLowerCase();
  if (classification !== "simple" && classification !== "complex") {
    console.warn(
      `  Unexpected classification "${classification}", defaulting to "complex".`
    );
    return "complex";
  }
  return classification;
}

// --- Step 2a: Direct Answer (Simple Path) ---

const directAnswerPrompt = ChatPromptTemplate.fromTemplate(
  `Answer this question clearly and concisely in 2-4 sentences:

{question}`
);

const directAnswerChain = directAnswerPrompt.pipe(llm).pipe(outputParser);

// --- Step 2b: Generate Sub-Questions (Complex Path) ---

const subQuestionsPrompt = ChatPromptTemplate.fromTemplate(
  `Break this complex question into 2-3 simpler sub-questions that,
when answered together, will fully address the original question.

Question: {question}

Return a JSON array of strings, e.g.: ["sub-question 1", "sub-question 2"]
Return ONLY the JSON array, no other text.`
);

const subQuestionsChain = subQuestionsPrompt.pipe(llm).pipe(outputParser);

// --- Step 2c: Answer a Sub-Question ---

const subAnswerPrompt = ChatPromptTemplate.fromTemplate(
  `Answer this question in 2-3 sentences. Be specific and informative.

Question: {subQuestion}`
);

const subAnswerChain = subAnswerPrompt.pipe(llm).pipe(outputParser);

// --- Step 3: Synthesize Answers ---

const synthesizePrompt = ChatPromptTemplate.fromTemplate(
  `You were asked: {originalQuestion}

Here are answers to related sub-questions:

{subAnswers}

Synthesize these into a single coherent answer (4-6 sentences).
Make sure the final answer directly addresses the original question.`
);

const synthesizeChain = synthesizePrompt.pipe(llm).pipe(outputParser);

// --- Step 4: Format Final Output as JSON ---

const formatPrompt = ChatPromptTemplate.fromTemplate(
  `Format this Q&A into a JSON object with these exact keys:
- "question": the original question (string)
- "answer": the answer (string)
- "confidence": your confidence in the answer ("high", "medium", or "low")
- "follow_up_questions": 2 related questions the user might ask next (array of strings)

Question: {question}
Answer: {answer}

Return ONLY valid JSON.`
);

const formatChain = formatPrompt.pipe(llm).pipe(outputParser);

// --- Main Workflow ---

async function researchWorkflow(question) {
  console.log("=".repeat(60));
  console.log("Research Assistant Workflow");
  console.log(`Question: "${question}"`);
  console.log("=".repeat(60));

  // Step 1: Classify
  console.log("\nStep 1: Classifying question complexity...");
  let classification;
  try {
    classification = await classifyQuestion(question);
    console.log(`  Classification: ${classification}`);
  } catch (error) {
    console.error(`  Classification failed: ${error.message}`);
    classification = "complex"; // Default to complex path on failure
    console.log("  Defaulting to complex path.");
  }

  let answer;

  if (classification === "simple") {
    // --- Simple Path ---
    console.log("\nStep 2: Generating direct answer...");
    try {
      answer = await callWithRetry(() =>
        directAnswerChain.invoke({ question })
      );
      console.log(`  Answer: ${answer}`);
    } catch (error) {
      console.error(`  Direct answer failed: ${error.message}`);
      return;
    }
  } else {
    // --- Complex Path ---

    // Step 2b: Generate sub-questions
    console.log("\nStep 2: Breaking into sub-questions...");
    let subQuestions;
    try {
      const rawSubQuestions = await withFallback(
        // Primary: ask for JSON array
        () => callWithRetry(() => subQuestionsChain.invoke({ question })),
        // Fallback: use a simpler prompt if JSON parsing fails
        async () => {
          console.warn("  Using fallback sub-question generation...");
          const fallbackPrompt = ChatPromptTemplate.fromTemplate(
            `List 2 simpler questions that help answer: {question}
             Format: one question per line, no numbers or bullets.`
          );
          const fallbackChain = fallbackPrompt.pipe(llm).pipe(outputParser);
          const result = await fallbackChain.invoke({ question });
          // Convert plain text lines to JSON array
          return JSON.stringify(
            result
              .split("\n")
              .map((q) => q.trim())
              .filter((q) => q.length > 0)
          );
        },
        "sub-questions"
      );

      // Parse and validate
      try {
        subQuestions = parseJsonOutput(rawSubQuestions);
        if (!Array.isArray(subQuestions) || subQuestions.length === 0) {
          throw new ValidationError("Expected non-empty array", rawSubQuestions);
        }
      } catch (validationError) {
        console.warn(`  JSON parse failed: ${validationError.message}`);
        // Last resort: split by newlines
        subQuestions = rawSubQuestions
          .split("\n")
          .map((q) => q.replace(/^[\d.\-*]+\s*/, "").trim())
          .filter((q) => q.length > 10);

        if (subQuestions.length === 0) {
          console.error("  Could not extract sub-questions. Aborting.");
          return;
        }
      }

      console.log(`  Sub-questions (${subQuestions.length}):`);
      subQuestions.forEach((q, i) => console.log(`    ${i + 1}. ${q}`));

      // Step 2c: Answer sub-questions IN PARALLEL
      console.log("\nStep 3: Answering sub-questions in parallel...");
      const subAnswerPromises = subQuestions.map((subQuestion, i) =>
        callWithRetry(() => subAnswerChain.invoke({ subQuestion }))
          .then((answer) => {
            console.log(`  [${i + 1}] Done.`);
            return { question: subQuestion, answer };
          })
          .catch((error) => {
            console.warn(`  [${i + 1}] Failed: ${error.message}`);
            return {
              question: subQuestion,
              answer: "(Could not generate answer)",
            };
          })
      );

      const subAnswers = await Promise.all(subAnswerPromises);

      // Format sub-answers for synthesis
      const formattedSubAnswers = subAnswers
        .map((sa) => `Q: ${sa.question}\nA: ${sa.answer}`)
        .join("\n\n");

      // Step 3: Synthesize
      console.log("\nStep 4: Synthesizing final answer...");
      try {
        answer = await callWithRetry(() =>
          synthesizeChain.invoke({
            originalQuestion: question,
            subAnswers: formattedSubAnswers,
          })
        );
        console.log(`  Synthesized answer: ${answer}`);
      } catch (error) {
        console.error(`  Synthesis failed: ${error.message}`);
        // Fallback: just concatenate the sub-answers
        answer = subAnswers.map((sa) => sa.answer).join(" ");
        console.log("  Using concatenated sub-answers as fallback.");
      }
    } catch (error) {
      console.error(`  Sub-question generation failed: ${error.message}`);
      return;
    }
  }

  // Step 4: Format as structured JSON
  console.log("\nStep 5: Formatting final output...");
  try {
    const rawFormatted = await callWithRetry(() =>
      formatChain.invoke({ question, answer })
    );

    const finalOutput = parseJsonOutput(rawFormatted, [
      "question",
      "answer",
      "confidence",
      "follow_up_questions",
    ]);

    console.log("\n" + "=".repeat(60));
    console.log("FINAL OUTPUT:");
    console.log("=".repeat(60));
    console.log(JSON.stringify(finalOutput, null, 2));
  } catch (error) {
    // Fallback: return unstructured answer
    console.warn(`  Formatting failed: ${error.message}`);
    console.log("\n" + "=".repeat(60));
    console.log("FINAL OUTPUT (unstructured fallback):");
    console.log("=".repeat(60));
    console.log(JSON.stringify({ question, answer }, null, 2));
  }
}

// --- Run ---

const question =
  process.argv[2] ||
  "What are the key differences between server-side rendering and client-side rendering, and when should you use each?";

await researchWorkflow(question);

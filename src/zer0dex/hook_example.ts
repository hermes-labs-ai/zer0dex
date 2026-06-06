/**
 * zer0dex Pre-Message Hook Example
 * 
 * This shows how to inject mem0 context into an agent's message pipeline.
 * Adapt this to your framework's message dispatch flow.
 * 
 * For an agent harness: this goes in src/auto-reply/dispatch.ts
 * For other frameworks: add before your LLM call.
 */

const MEM0_SERVER = "http://127.0.0.1:18420";
const MEM0_TIMEOUT_MS = 500;

interface Mem0Memory {
  text: string;
  score: number;
}

interface Mem0Response {
  memories?: Mem0Memory[];
}

/**
 * Query the zer0dex memory server.
 * Returns an array of context strings to inject into the agent's context.
 * Returns empty array on failure (graceful degradation).
 */
async function queryZer0dex(messageText: string): Promise<string[]> {
  if (!messageText || messageText.trim().length < 5) return [];

  try {
    const controller = new AbortController();
    const timeout = setTimeout(() => controller.abort(), MEM0_TIMEOUT_MS);

    const res = await fetch(`${MEM0_SERVER}/query`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ text: messageText.slice(0, 500), limit: 5 }),
      signal: controller.signal,
    });

    clearTimeout(timeout);
    if (!res.ok) return [];

    const data = (await res.json()) as Mem0Response;
    const memories = data.memories ?? [];
    if (memories.length === 0) return [];

    // Format as a single context string
    return [`[mem0 context] ${memories.map((m) => m.text).join(" | ")}`];
  } catch {
    // Server not running or timed out — silently skip
    return [];
  }
}

// --- Integration example ---
// In your message handler, before calling the LLM:
//
// const mem0Context = await queryZer0dex(userMessage);
// if (mem0Context.length > 0) {
//   // Inject as additional context (NOT as system instructions)
//   messageContext.untrustedContext = [
//     ...(messageContext.untrustedContext ?? []),
//     ...mem0Context,
//   ];
// }

export { queryZer0dex };

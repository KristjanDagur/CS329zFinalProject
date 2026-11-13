// OpenCode 1.19.5 native plugin; the host serves only the support partition.
export const IntentTools = async () => {
  const invoke = async (name, body, context) => {
    const response = await fetch(process.env.INTENT_TOOL_URL + '/tools/' + name, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', Authorization: 'Bearer ' + process.env.INTENT_TOOL_TOKEN },
      body: JSON.stringify({ ...body, session_id: context.sessionID }),
    });
    if (!response.ok) throw new Error('Bounded retrieval failed: ' + response.status);
    return JSON.stringify(await response.json());
  };
  return {
    'chat.headers': async (input, output) => { output.headers['x-intent-session'] = input.sessionID; },
    tool: {
      search_examples: {
        description: 'Search real labeled BANKING77 support examples using BM25. Returns at most eight cases with support_id, text, intent, and score. Required at least once before the final answer.',
        args: { query: { type: 'string', description: 'The banking utterance or a focused search for its meaning.' } },
        execute: async (args, context) => invoke('search', { query: args.query }, context),
      },
      lookup_intent: {
        description: 'Look up one canonical intent and its fixed support exemplar. Counts against the two-tool-call limit.',
        args: { intent: { type: 'string', description: 'An exact canonical intent from the catalog.' } },
        execute: async (args, context) => invoke('lookup', { intent: args.intent }, context),
      },
    },
  };
};

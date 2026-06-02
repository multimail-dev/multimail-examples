# OpenAI Function Calling + MultiMail

A conversational email agent that uses GPT-4o with OpenAI's function calling API to manage email through [MultiMail](https://multimail.dev).

The agent can:

- Check your inbox and summarize new emails
- Read full email content
- Send new emails (markdown body, auto-converted to HTML)
- Reply to email threads
- Search your address book
- Review emails pending oversight approval

This example sits alongside MultiMail's 38 MCP tools and uses the same delivery and compliance layer.

## Setup

1. Install dependencies:

```bash
pip install -r requirements.txt
```

2. Set environment variables:

```bash
export OPENAI_API_KEY="sk-..."
export MULTIMAIL_API_KEY="mm_live_..."
```

3. Edit `openai_email_agent.py` and set your `MAILBOX_ID` at the top of the file. You can find your mailbox ID in the [MultiMail dashboard](https://multimail.dev).

4. Run:

```bash
python openai_email_agent.py
```

## How it works

The script defines six MultiMail operations as OpenAI function schemas. When you type a request, GPT-4o decides which functions to call, the script executes them against the MultiMail API via the Python SDK, and feeds the results back to the model for a natural language response.

Example:

```
You: Check my inbox and summarize any unread emails

  -> Calling check_inbox({"status": "unread"})

Assistant: You have 3 unread emails:
1. From alice@example.com - "Q1 Report" - Quarterly metrics summary
2. From bob@example.com - "Lunch tomorrow?" - Asking about lunch plans
3. From notifications@example.com - "PR Review" - Review requested on PR #42
```

## Compliance

MultiMail handles regulatory compliance at the infrastructure layer — no SDK-side code changes needed:

- **EU AI Act Article 50**: Every AI-sent email includes a cryptographically signed `ai_generated` disclosure in the `X-MultiMail-Identity` header
- **US State Laws**: Maine, New York, California, Illinois — AI disclosure built into email delivery
- **CAN-SPAM**: Unsubscribe headers and physical address footers on all outbound email
- **Formally Verified**: Lean 4 proofs of identity header tamper evidence

Compliance example: see [multimail.dev/use-cases/eu-ai-act-email-compliance](https://multimail.dev/use-cases/eu-ai-act-email-compliance) for the end-to-end AI disclosure flow.

## Learn more

- [MultiMail documentation](https://multimail.dev)
- [OpenAI function calling guide](https://platform.openai.com/docs/guides/function-calling)
- [MultiMail Python SDK](https://pypi.org/project/multimail/)

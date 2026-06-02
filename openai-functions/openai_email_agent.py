"""
OpenAI Function Calling + MultiMail Example

A conversational email agent that uses GPT-4o with OpenAI's function calling
to manage email through the MultiMail API. The agent can check your inbox,
read emails, send new messages, reply to threads, search contacts, and
review pending oversight emails.

Usage:
    export OPENAI_API_KEY="sk-..."
    export MULTIMAIL_API_KEY="mm_live_..."
    python openai_email_agent.py
"""

import json
import os

from multimail import MultiMail
from openai import OpenAI

# --- Configuration ---

MAILBOX_ID = "YOUR_MAILBOX_ID"  # Replace with your mailbox ID

client = OpenAI(api_key=os.environ["OPENAI_API_KEY"])
mm = MultiMail(api_key=os.environ["MULTIMAIL_API_KEY"])

# --- Function Schemas ---

TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "check_inbox",
            "description": (
                "List emails in the inbox. Returns summaries with id, from, to, "
                "subject, status, and received_at. Does NOT include the email body."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "status": {
                        "type": "string",
                        "enum": [
                            "unread", "read", "archived", "deleted",
                            "pending_send_approval", "pending_inbound_approval",
                        ],
                        "description": "Filter by email status",
                    },
                    "sender": {
                        "type": "string",
                        "description": "Filter by sender email (partial match)",
                    },
                    "subject_contains": {
                        "type": "string",
                        "description": "Filter by subject text (partial match)",
                    },
                    "limit": {
                        "type": "integer",
                        "description": "Max results (default 20, max 100)",
                    },
                },
                "required": [],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "read_email",
            "description": (
                "Get the full content of a specific email including the markdown "
                "body and attachment metadata. Marks unread emails as read."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "email_id": {
                        "type": "string",
                        "description": "The email ID to read",
                    },
                },
                "required": ["email_id"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "send_email",
            "description": (
                "Send an email. The body is written in markdown and converted to "
                "HTML for delivery. Returns the email ID and status."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "to": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Recipient email addresses",
                    },
                    "subject": {
                        "type": "string",
                        "description": "Email subject line",
                    },
                    "markdown": {
                        "type": "string",
                        "description": "Email body in markdown format",
                    },
                    "cc": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "CC email addresses",
                    },
                },
                "required": ["to", "subject", "markdown"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "reply_email",
            "description": (
                "Reply to an email in its existing thread. Threading headers are "
                "set automatically. The body is written in markdown."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "email_id": {
                        "type": "string",
                        "description": "The email ID to reply to",
                    },
                    "markdown": {
                        "type": "string",
                        "description": "Reply body in markdown format",
                    },
                },
                "required": ["email_id", "markdown"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "search_contacts",
            "description": (
                "Search your address book by name or email. Returns matching "
                "contacts with their tags. Call with no query to list all."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Search by name or email (partial match)",
                    },
                },
                "required": [],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "list_pending",
            "description": (
                "List emails awaiting oversight decision (pending approval). "
                "Use this to review emails before approving or rejecting them."
            ),
            "parameters": {
                "type": "object",
                "properties": {},
                "required": [],
            },
        },
    },
]

# --- Function Dispatch ---


def call_function(name: str, args: dict) -> str:
    """Route a function call to the MultiMail SDK and return the JSON result."""
    if name == "check_inbox":
        result = mm.check_inbox(mailbox_id=MAILBOX_ID, **args)
    elif name == "read_email":
        result = mm.read_email(
            mailbox_id=MAILBOX_ID, email_id=args["email_id"],
        )
    elif name == "send_email":
        result = mm.send_email(mailbox_id=MAILBOX_ID, **args)
    elif name == "reply_email":
        result = mm.reply_email(
            mailbox_id=MAILBOX_ID,
            email_id=args["email_id"],
            markdown=args["markdown"],
        )
    elif name == "search_contacts":
        result = mm.search_contacts(**args)
    elif name == "list_pending":
        result = mm.list_pending()
    else:
        return json.dumps({"error": f"Unknown function: {name}"})

    return json.dumps(result, default=str)


# --- Agent Loop ---

SYSTEM_PROMPT = (
    "You are an email assistant powered by MultiMail. You can check the inbox, "
    "read emails, send new messages, reply to threads, search contacts, and "
    "review pending emails. Be concise and helpful. When summarizing emails, "
    "include the sender, subject, and a brief summary. Ask before sending or "
    "replying to confirm the user wants to proceed."
)


def run_agent(user_message: str):
    """Run the agent loop: send message to GPT-4o, handle tool calls, repeat."""
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": user_message},
    ]

    while True:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=messages,
            tools=TOOLS,
        )

        choice = response.choices[0]
        message = choice.message
        messages.append(message)

        # If the model is done (no tool calls), print and return
        if not message.tool_calls:
            print(f"\nAssistant: {message.content}")
            return

        # Process each tool call
        for tool_call in message.tool_calls:
            fn_name = tool_call.function.name
            fn_args = json.loads(tool_call.function.arguments)

            print(f"  -> Calling {fn_name}({json.dumps(fn_args, indent=2)})")

            result = call_function(fn_name, fn_args)

            messages.append({
                "role": "tool",
                "tool_call_id": tool_call.id,
                "content": result,
            })


# --- Main ---

if __name__ == "__main__":
    print("MultiMail + OpenAI Function Calling Agent")
    print("=" * 44)
    print("Type your request (or 'quit' to exit).\n")

    while True:
        user_input = input("You: ").strip()
        if not user_input or user_input.lower() in ("quit", "exit", "q"):
            break
        run_agent(user_input)
        print()

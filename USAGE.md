# How to Use These Skills in Any LLM

This guide explains how to make the skills in this repo work with any LLM (GPT, Claude, Gemini, Llama, etc.).

## What Are These Skills?

Each folder in `skills/` contains a `SKILL.md` file following an open, LLM-agnostic format:
- **Frontmatter**: machine-readable metadata (name, description, version)
- **Instructions**: step-by-step guidance any LLM can follow
- **Input/Output patterns**: how to structure calls and responses
- **Safety rules**: built-in guardrails

## Option 1: System Prompt Injection (Simplest)

Copy the contents of a `SKILL.md` into your LLM's system prompt or context:

```
You have access to the following skill:

[ paste SKILL.md content here ]

Follow its instructions when the user asks for related tasks.
```

## Option 2: RAG / Vector Store

1. Index all `SKILL.md` files in a vector database
2. When a user asks something, retrieve the most relevant skill(s)
3. Inject the retrieved skill(s) into the prompt
4. Let the LLM follow the skill's instructions

## Option 3: Function Calling / Tool Use

Convert each skill into your LLM provider's function definition:

**OpenAI / Anthropic / Gemini**:
```python
# Example: convert SKILL.md frontmatter to function schema
{
    "name": "github",
    "description": "Search and work with GitHub repositories...",
    "parameters": {
        "type": "object",
        "properties": {
            "query": {"type": "string", "description": "What to search for"},
            # Add more based on the skill's needs
        }
    }
}
```

Then map function calls to actual API implementations in your backend.

## Option 4: Agent Frameworks

These skills work with popular agent frameworks:

- **LangChain**: Load SKILL.md as a `Tool` with the description as the tool description
- **AutoGen**: Register each skill as an agent capability
- **CrewAI**: Add skills as agent tools
- **LlamaIndex**: Use as query engine tools

Example with LangChain:
```python
from langchain.tools import Tool
import frontmatter

# Load a skill
with open('skills/github/SKILL.md') as f:
    post = frontmatter.load(f)
    
tool = Tool(
    name=post['name'],
    description=post['description'],
    func=your_github_implementation  # You implement this
)
```

## What You Need to Implement

The `SKILL.md` files provide the **instruction layer**. You still need the **execution layer**:

| Skill Needs | You Provide |
|-------------|-------------|
| API calls | HTTP client + credentials |
| OAuth | Your auth flow |
| Data storage | Your database |
| Web browsing | Your browsing tool |

The skill tells the LLM *what* to do and *how* to think. Your code provides the *ability* to do it.

## Safety Notes

All skills include safety rules, but you should also:
1. Implement user confirmation for write operations in your UI
2. Never expose credentials to the LLM's output
3. Validate all LLM-generated API parameters before executing
4. Log skill usage for auditability

## Contributing

To add a new universal skill:
1. Create `skills/your-skill/SKILL.md` following the existing format
2. Include frontmatter with name, description, version
3. Write LLM-agnostic instructions (no vendor-specific tool names)
4. Submit a PR

---

*These skills are designed to be 99% portable. The 1% that's missing is your execution environment — which you control.*

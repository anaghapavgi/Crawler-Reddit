# Start Here

This prompt pack is designed for Cursor Agent or Google Antigravity.

## Recommended use

1. Create an empty Git repository.
2. Copy the contents of this pack into the repository root.
3. Open the repository in Cursor or Antigravity.
4. Review `MANUAL_SETUP_CHECKLIST.md` but do not add secrets yet.
5. Paste the complete contents of `MASTER_BUILD_PROMPT.md` into the coding agent.
6. Ask the agent to operate in plan-and-execute mode and remain inside the repository.
7. Let it complete phases using demo mode first.
8. Add credentials only after the demo, tests, and secret protections work.
9. Use `PHASE_PROMPTS.md` if the agent loses context or tries to build too much at once.
10. Use `ACCEPTANCE_CHECKLIST.md` before considering the project complete.

## Best safety setting

Require approval for commands that delete files, change system configuration, install global packages, access folders outside the repository, or transmit data. Allow normal project-local editing, virtual-environment package installation, tests, and browser verification.

## Expected outputs

The coding agent should produce a full Python repository, not only code snippets. It must include demo data, tests, SQL migration, GitHub Actions, documentation, and a deployable Streamlit app.

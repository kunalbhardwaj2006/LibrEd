# Contributing to LibrEd

Thank you for your interest in contributing to LibrEd!

This guide helps new contributors set up the project, understand
the system architecture, and submit their first contribution.

---

# Project Overview

LibrEd is an open-source platform designed to help students prepare
for the GATE (Graduate Aptitude Test in Engineering) examination.

The platform consists of two primary components:

• **Generator** – builds the dataset by processing PDFs and using local LLMs  
• **Frontend** – a React interface for studying generated content  

The generator produces structured study assets that the frontend
automatically discovers and renders.

---

# Development Environment Setup

## 1. Clone the Repository


git clone https://github.com/AOSSIE-Org/LibrEd.git

cd LibrEd

---


---

## 2. Start the Platform

Run the platform using Docker:
docker compose up --build

This command starts all required services.

The frontend will be available at:


http://localhost:3000


---

# Understanding the Generator

The generator is responsible for building the study dataset.

Pipeline stages include:

1. Download PDFs  
2. Extract questions  
3. Synchronize with database  
4. Generate classification prompts  
5. Process prompts using a local LLM  
6. Generate theory explanations  
7. Build dataset manifests  

Each stage consumes artifacts produced by earlier stages.

More detailed architecture documentation can be found in:


generator/ARCHITECTURE.md


---

# Running Tests

Before submitting changes, contributors should run tests to ensure
that the generator pipeline continues to function correctly.

Run generator tests using Docker:


docker compose run --rm asset-generator pytest generator/tests


---

# First Contribution Ideas

New contributors can begin with small improvements such as:

### Documentation Improvements

• Improve README clarity  
• Expand architecture documentation  
• Improve developer onboarding guides  

### Generator Improvements

• Improve logging and error handling  
• Add pipeline performance improvements  
• Improve PDF extraction heuristics  

### Dataset Expansion

• Add support for additional exam streams  
• Extend question bank datasets  

---

# Submitting a Pull Request

Follow these steps to submit a contribution:

1. Fork the repository  
2. Create a new branch  
3. Implement your changes  
4. Commit with a clear message  
5. Open a Pull Request

Example branch naming conventions:


feat/generator-new-stage
fix/pdf-parsing-error
docs/update-readme


Describe your changes clearly in the PR description and link any
related issues.

---

# Code Quality

Before submitting a PR:

• Ensure tests pass  
• Follow the project structure  
• Write clear commit messages  
• Keep pull requests focused and small  

---

# Community

We welcome contributions from developers of all experience levels.

If you have questions, feel free to open a discussion or ask in the
community channels.

Happy contributing!
docker compose up --build


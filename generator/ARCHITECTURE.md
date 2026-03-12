# Generator Architecture

This document explains the architecture of the LibrEd asset generator
pipeline and how contributors can extend it.

The generator is responsible for transforming raw syllabus PDFs into
structured study datasets used by the frontend.

---

# Overview

The generator is implemented as a sequential processing pipeline.

Each stage produces artifacts that are consumed by later stages.

Pipeline flow:

Download PDFs
→ Extract Questions
→ Database Synchronization
→ Classification Prompt Generation
→ LLM Classification
→ Theory Prompt Generation
→ LLM Theory Generation
→ Manifest Creation

---
## Pipeline Architecture Diagram

The following diagram illustrates the high-level data flow of the generator pipeline.

```mermaid
flowchart LR

A[PDF Sources]
B[PDF Download Stage]
C[Question Extraction]
D[Database Sync]
E[Prompt Generation]
F[LLM Classification]
G[Theory Generation]
H[Manifest Builder]
I[Frontend Dataset]

A --> B
B --> C
C --> D
D --> E
E --> F
F --> G
G --> H
H --> I

```markdown
# Data Flow

The generator processes content in a linear pipeline where each
stage produces artifacts consumed by the next stage.

Data flow example:

PDF files
→ extracted question images
→ structured question metadata
→ topic classification prompts
→ classified questions
→ generated theory explanations
→ dataset manifest files

Each artifact is stored locally so the pipeline can resume safely
without reprocessing completed steps.

# Pipeline Stages

## 1. PDF Download

The generator downloads syllabus or question bank PDFs for the
configured exam streams.

These files are stored in the dataset directory and used as the
initial source of raw content.

---

## 2. Question Extraction

The generator parses PDFs using PyMuPDF.

This stage extracts:

- question images
- page references
- structural metadata

Artifacts are stored locally before database synchronization.

---

## 3. Database Synchronization

Extracted questions are synchronized with the DuckDB database.

This ensures the dataset remains consistent and prevents duplicate
processing when the generator is executed multiple times.

---

## 4. Classification Prompt Generation

For each question the generator constructs prompts used to classify
the question into topics.

Prompts are stored in a queue for LLM processing.

---

## 5. LLM Classification

Prompts are processed using a locally running LLM through Ollama.

The model assigns topic categories to each question.

Example models:

- llama3
- mistral
- gemma
- phi

---

## 6. Theory Prompt Generation

After classification the generator prepares prompts for generating
theoretical explanations for each topic.

These prompts request conceptual explanations from the model.

---

## 7. Theory Generation

The LLM generates explanations and supporting theory for each topic.

Outputs are stored in the dataset so the frontend can display them.

---

## 8. Manifest Generation

Finally the generator creates manifest files that allow the frontend
to automatically discover generated datasets.

The frontend dynamically loads these manifests to build navigation.

---

# Directory Structure

generator/

src/  
core pipeline logic

config.py  
generator configuration

tests/  
automated test suite

requirements.txt  
python dependencies

---

# Idempotent Pipeline Design

The generator pipeline is designed to be idempotent.

Running the generator multiple times will:

- skip previously processed data
- process only missing artifacts
- extend existing datasets safely

This allows the generator to run repeatedly without corrupting
existing data.

---

# Extending the Generator

Contributors can extend the generator in several ways.

Examples include:

• adding new exam streams  
• improving extraction heuristics  
• adding additional LLM prompt strategies  
• optimizing pipeline performance  

When modifying the generator pipeline ensure that:

1. stages remain deterministic  
2. database consistency is preserved  
3. outputs remain compatible with frontend manifests

## Example: Adding a New Pipeline Stage

To add a new stage to the generator pipeline:

1. Create a new module inside `generator/src`.
2. Implement the stage logic as a function.
3. Register the stage in the main pipeline execution flow.
4. Ensure the stage produces deterministic outputs.

Example:

```python
def generate_embeddings(questions):
    # Example extension stage
    embeddings = embedding_model.encode(questions)
    return embeddings

---

# Development Workflow

Recommended development workflow:

1. run the generator locally with Docker
2. observe logs during pipeline execution
3. modify pipeline stages
4. run tests before submitting pull requests

Example command:

docker compose up --build

---
# Pipeline Execution Example

Below is a simplified example of how the generator pipeline runs
when the project is started with Docker.

Example command:

docker compose up --build

Typical execution flow:

1. The generator container starts.
2. Configuration is loaded from `generator/src/config.py`.
3. Target exam streams are identified.
4. PDFs are downloaded or verified locally.
5. Questions are extracted from PDFs using PyMuPDF.
6. Extracted data is synchronized with DuckDB.
7. Classification prompts are generated.
8. Prompts are processed using the configured Ollama model.
9. Theory explanations are generated.
10. Manifest files are created for frontend discovery.

During execution logs are produced for each stage, allowing
developers to monitor pipeline progress and debug issues.

# Future Improvements

Potential future enhancements include:

• parallel pipeline execution  
• caching of LLM responses  
• improved PDF parsing heuristics  
• evaluation of different LLM models  

Contributions in these areas are welcome.

```markdown
# Related Documentation

Additional project documentation:

- Project Architecture: ../arch.md
- Contributor Guide: ../CONTRIBUTING.md
- Project Overview: ../README.md

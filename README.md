> [!IMPORTANT]
> The README is currently being improved. For a deeper understanding of the system architecture and design decisions, please read [arch.md](./arch.md).

# Dont Compete

**Dont Compete** is a fully local, containerized, and agent-driven platform designed to help students prepare for the **GATE (Graduate Aptitude Test in Engineering)** examination.

The platform combines a **modern React frontend** with an **autonomous backend pipeline** that scrapes, classifies, and generates structured study materials from syllabus PDFs using **local LLMs**.

The goal of this project is to build a **high-quality, privacy-first, open learning platform** for competitive exam preparation.

---

# Core Philosophy

The platform is designed around three key principles.

## 1. 100% Local & Private

All data processing and AI generation happen **locally on your machine** using **Ollama**.

This means:

- No external APIs  
- No cloud dependencies  
- No user data leaving your system  

This ensures **maximum privacy and reproducibility**.

---

## 2. Container-First Architecture

The entire platform runs using **Docker Compose**.

Contributors **do not need to install Python, Node.js, or additional dependencies locally**.

Everything runs inside containers which provides:

- consistent development environments  
- simplified setup  
- reproducible builds  

---

## 3. Autonomous Asset Generator

The backend generator is a **functional pipeline** responsible for transforming raw syllabus PDFs into structured study content.

Key characteristics:

### Sequential Pipeline

Download → OCR → Database Sync → Classification → Theory Generation → Manifest Creation

### Deterministic Processing

Heuristic parsing ensures **high-fidelity extraction of questions, answers, and explanations** from PDFs.

### Idempotent Execution

Running the pipeline multiple times will **extend existing datasets rather than overwrite them**.

---

# System Architecture

The platform consists of two independent components that communicate through shared filesystem artifacts.

## 1. Asset Generator (`/generator`)

A Python-based pipeline responsible for dataset generation.

Technologies used:

- DuckDB — local database  
- PyMuPDF — PDF parsing  
- Tenacity — retry logic  
- Ollama — local LLM inference  

Responsibilities include:

- scraping syllabus PDFs  
- extracting question images  
- classifying questions into topics  
- generating theory explanations  
- building manifest files for frontend discovery  

---

## 2. Frontend (`/frontend`)

A modern **React application** that dynamically discovers generated study content.

Tech stack:

- Vite  
- TanStack Router  
- Modular component architecture  

Features:

- zero-configuration content discovery  
- dynamic navigation  
- adaptive assessment interface  

The frontend reads generated assets directly from the filesystem.

---

# Getting Started

## Prerequisites

Install the following tools:

- Docker Desktop  
  https://docs.docker.com/get-docker/

or

- Docker Engine + Docker Compose

Also install:

- Git  
  https://git-scm.com/

---

# Quick Start

## 1. Clone the Repository

```bash
git clone https://github.com/AOSSIE-Org/LibrEd.git
cd LibrEd
2. Launch the Platform
docker compose up --build

This command starts all services.

Frontend will be available at:

http://localhost:3000

The generator will automatically begin populating content in the background.

If the pipeline has already run previously, it will skip existing data and process only new or missing streams.

3. Monitor the Pipeline

To view generator logs in real time:

docker compose logs -f asset-generator

This helps monitor progress during dataset generation.

Pipeline Overview

The asset generator processes content through multiple stages:

Download PDFs

Extract questions and assets from PDFs

Synchronize assets with database

Generate classification prompts

Process prompts using local LLM

Generate theory explanations

Process theory prompts

Generate manifest files for frontend discovery

Each stage builds upon outputs produced by earlier stages.

Configuration

Generator configuration is located at:

generator/src/config.py

Important parameters include:

TARGET_STREAMS

Defines which exam streams should be processed.

Example:

TARGET_STREAMS = ["CS", "DA"]
OLLAMA_MODEL

Defines which local LLM model will be used.

Default model:

llama3.1

You can experiment with other models such as:

Mistral

Gemma

Phi-3

Different models may produce different theory explanations.

Contributing

We are building a free and open study platform, and contributions are welcome.

Both technical and non-technical contributions are valuable.

Non-Coding Contributions

AI-generated explanations may sometimes lack clarity or depth. Community contributions help improve content quality.

Improve Theory Content

You can improve explanations by adding:

clearer reasoning

examples

diagrams

alternative explanations

Quality Assurance

Help validate question correctness.

Tasks include:

reviewing pull requests

verifying answers

suggesting corrections

Model Evaluation

Run the generator using different LLM models and report which models produce the best results.

Expand Dataset

Add support for:

additional exam streams

more question banks

other competitive exams

Testing

The project includes automated test suites.

Generator Tests (Backend)

Run backend tests using Docker:

docker compose run --rm asset-generator pytest generator/tests
Frontend Tests

Run end-to-end tests using the official Playwright container:

docker run --rm --network gatebuster_app_network \
-e BASE_URL=http://frontend:3000 \
-v $(pwd)/frontend:/app \
-w /app \
mcr.microsoft.com/playwright:v1.58.0-jammy \
/bin/sh -c "npm install && npx playwright test"
Windows PowerShell
docker run --rm --network gatebuster_app_network `
-e BASE_URL=http://frontend:3000 `
-v ${PWD}/frontend:/app `
-w /app `
mcr.microsoft.com/playwright:v1.58.0-jammy `
sh -c "npm install && npx playwright test"

Ensure the frontend service is running before executing tests:

docker compose up
License

This project is licensed under the Apache 2.0 License.

See the LICENSE file for details.

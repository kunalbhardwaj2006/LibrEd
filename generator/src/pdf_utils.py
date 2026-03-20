import fitz  # PyMuPDF
import os
import logging
import re
from PIL import Image
import asyncio
import json

from generator.src.config import (
    GATE_ASSETS_DIR, 
    STREAM_ALIASES,
    IMAGE_FORMAT,
    IMAGE_QUALITY,
    IMAGE_LOSSLESS,
    PDF_ZOOM_LEVEL
)
from generator.src.image_utils import optimize_image, get_file_extension
from generator.src.llm_utils import generate_text

logger = logging.getLogger(__name__)

# Regex Patterns
RE_Q_START = re.compile(r'^\s*Question\s*\d+', re.IGNORECASE)
RE_ANS_START = re.compile(r'^\s*Ans\.\s*', re.IGNORECASE)
RE_SOL_START = re.compile(r'^\s*Sol\.\s*', re.IGNORECASE)
RE_PAGE_ARTIFACT = re.compile(r'^\s*PAGE\s*\d+', re.IGNORECASE)

# ------------------------- PROCESS STREAM -------------------------
def process_stream(stream_code):
    stream_alias = STREAM_ALIASES.get(stream_code, stream_code)
    stream_dir = os.path.join(os.path.abspath("data/raw"), stream_alias)
    
    if not os.path.exists(stream_dir):
        logger.warning(f"No raw data found for {stream_code} at {stream_dir}")
        return

    for filename in os.listdir(stream_dir):
        if not filename.endswith(".pdf"):
            continue
            
        filepath = os.path.join(stream_dir, filename)
        process_pdf(stream_code, filepath)

# ------------------------- PROCESS PDF -------------------------
def process_pdf(stream, filepath):
    fname = os.path.basename(filepath)
    packet_id = os.path.splitext(fname)[0]  # e.g. "2021-M"

    year = "Unknown"
    match_year = re.search(r'(\d{4})', packet_id)
    if match_year:
        year = match_year.group(1)

    logger.info(f"Processing PDF {packet_id} (Year: {year})")
    doc = fitz.open(filepath)

    # --- State Machine ---
    current_state = None  # 'QUESTION', 'ANSWER', 'EXPLANATION'
    current_q_meta = {}
    processed_questions = []

    def flush_question():
        nonlocal current_q_meta
        if current_q_meta and current_q_meta.get('id'):
            processed_questions.append(current_q_meta.copy())
        return {
            'id': None,
            'q_text': [], 'q_rects': [],
            'a_text': [],
            'exp_text': [], 'exp_rects': [],
            'type': 'MCQ'
        }

    current_q_meta = flush_question()

    # --- Parse PDF pages ---
    for page_num, page in enumerate(doc):
        blocks = page.get_text("dict")["blocks"]
        sorted_blocks = sorted(blocks, key=lambda b: (b['bbox'][1], b['bbox'][0]))

        for block in sorted_blocks:
            if 'lines' not in block:
                continue

            block_text = "\n".join([span['text'] for line in block['lines'] for span in line['spans']]).strip()
            bt_lower = block_text.lower()

            if RE_PAGE_ARTIFACT.match(block_text) or "gate academy" in bt_lower or "general aptitude" in bt_lower:
                continue

            # --- State Transitions ---
            if RE_Q_START.match(block_text):
                current_q_meta = flush_question()
                raw_id = block_text.split()[1] if len(block_text.split()) > 1 else "Unknown"
                current_q_meta['id'] = raw_id.rstrip('.')
                current_state = 'QUESTION'
                current_q_meta['q_text'].append(block_text)
                current_q_meta['q_rects'].append((page_num, block['bbox']))

            elif RE_ANS_START.match(block_text):
                current_state = 'ANSWER'
                current_q_meta['a_text'].append(block_text)

            elif RE_SOL_START.match(block_text):
                current_state = 'EXPLANATION'
                current_q_meta['exp_text'].append(block_text)
                current_q_meta['exp_rects'].append((page_num, block['bbox']))

            else:
                if current_state == 'QUESTION':
                    current_q_meta['q_text'].append(block_text)
                    current_q_meta['q_rects'].append((page_num, block['bbox']))
                elif current_state == 'ANSWER':
                    current_q_meta['a_text'].append(block_text)
                elif current_state == 'EXPLANATION':
                    current_q_meta['exp_text'].append(block_text)
                    current_q_meta['exp_rects'].append((page_num, block['bbox']))

    # Flush last question
    current_q_meta = flush_question()
    logger.info(f"Extracted {len(processed_questions)} raw questions.")

    # --- Async Theory Generation ---
    async def generate_theory_for_questions(processed_questions):
        batch_size = 5
        async def worker(batch):
            return await asyncio.gather(*[
                asyncio.to_thread(generate_text, "Generate theory: " + " ".join(q['q_text']))
                for q in batch
            ])

        batches = [processed_questions[i:i + batch_size] for i in range(0, len(processed_questions), batch_size)]
        for batch in batches:
            batch_results = await worker(batch)
            for q, theory in zip(batch, batch_results):
                q['exp_text'] = [theory]

    asyncio.run(generate_theory_for_questions(processed_questions))

    # --- Save Questions ---
    for q_data in processed_questions:
        try:
            save_question_data(stream, packet_id, year, q_data, doc)
        except Exception as e:
            logger.error(f"Error saving question {q_data.get('id')}: {e}")

# ------------------------- SAVE QUESTION -------------------------
def save_question_data(stream, packet_id, year, q_data, doc):
    q_id_str = q_data['id']
    stream_alias = STREAM_ALIASES.get(stream, stream)
    q_clean_id = q_id_str.replace(' ', '')

    q_text_full = "\n".join(q_data['q_text'])
    a_text_full = "\n".join(q_data['a_text']).replace("Ans.", "").strip()
    exp_text_full = "\n".join(q_data['exp_text'])

    img_ext = get_file_extension(IMAGE_FORMAT)
    base_rel_path = f"{stream_alias}/questions/{packet_id}/{q_clean_id}"
    base_abs_path = os.path.join(GATE_ASSETS_DIR, base_rel_path)
    os.makedirs(base_abs_path, exist_ok=True)

    q_img_abs_path = os.path.join(base_abs_path, f"q{img_ext}")
    exp_img_abs_path = os.path.join(base_abs_path, f"exp{img_ext}")

    create_stitched_image(doc, q_data['q_rects'], q_img_abs_path)
    if q_data['exp_rects']:
        create_stitched_image(doc, q_data['exp_rects'], exp_img_abs_path)

    q_type = "MCQ"
    if "MSQ" in q_text_full: q_type = "MSQ"
    if "NAT" in q_text_full or "Numerical" in q_text_full: q_type = "NAT"

    try:
        data = {
            "id": q_id_str,
            "stream": stream,
            "packet": packet_id,
            "year": year,
            "type": q_type,
            "key": a_text_full,
            "question_text": q_text_full,
            "answer_text": a_text_full,
            "explanation_text": exp_text_full
        }
        with open(os.path.join(base_abs_path, "data.json"), "w") as f:
            json.dump(data, f, indent=2)
    except Exception as e:
        logger.error(f"Failed to write data json for {q_id_str}: {e}")
    logger.info(f"Saved Question {q_id_str}")

# ------------------------- CREATE STITCHED IMAGE -------------------------
def create_stitched_image(doc, rects_info, output_path):
    if not rects_info: return
    pages_map = {}
    for page_num, bbox in rects_info:
        if page_num not in pages_map:
            pages_map[page_num] = {'min_y': bbox[1], 'max_y': bbox[3]}
        else:
            pages_map[page_num]['min_y'] = min(pages_map[page_num]['min_y'], bbox[1])
            pages_map[page_num]['max_y'] = max(pages_map[page_num]['max_y'], bbox[3])

    images = []
    for page_num in sorted(pages_map.keys()):
        page = doc[page_num]
        y_min = pages_map[page_num]['min_y']
        y_max = pages_map[page_num]['max_y']
        rect = fitz.Rect(0, y_min, page.rect.width, y_max)
        pix = page.get_pixmap(clip=rect, matrix=fitz.Matrix(PDF_ZOOM_LEVEL, PDF_ZOOM_LEVEL))
        img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
        images.append(img)

    total_height = sum(img.height for img in images)
    max_width = max(img.width for img in images)
    final_img = Image.new('RGB', (max_width, total_height), (255, 255, 255))

    y_offset = 0
    for img in images:
        final_img.paste(img, (0, y_offset))
        y_offset += img.height

    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    optimize_image(final_img, output_path, format=IMAGE_FORMAT, quality=IMAGE_QUALITY, lossless=IMAGE_LOSSLESS)

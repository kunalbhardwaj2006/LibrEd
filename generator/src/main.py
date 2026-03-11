import asyncio
import logging
import sys
import os
from tqdm import tqdm

from generator.src.config import (
    TARGET_STREAMS,
    GATE_ASSETS_DIR,
    CLASSIFICATION_BATCH_SIZE,
    TEST_PROMPT_LIMIT,
)

from generator.src.scraper_engine import ScraperEngine
from generator.src.model_manager import ensure_model_available

# Functional Modules
import generator.src.pdf_utils as pdf_utils
import generator.src.prompt_utils as prompt_utils
import generator.src.knowledge_utils as knowledge_utils
import generator.src.db_utils as db_utils


# -------------------------
# Logging Configuration
# -------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(name)s | %(levelname)s | %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)

logger = logging.getLogger("AssetGenerator")


# -------------------------
# Helper: Stage Header
# -------------------------
def stage_header(title: str):
    logger.info("=" * 60)
    logger.info(title)
    logger.info("=" * 60)


# -------------------------
# Main Pipeline
# -------------------------
async def main():

    logger.info("Starting Asset Generator Pipeline")

    # Ensure model availability
    if not ensure_model_available():
        logger.error("Model availability check failed. Exiting pipeline.")
        sys.exit(1)

    # Ensure asset directory exists
    os.makedirs(GATE_ASSETS_DIR, exist_ok=True)

    scraper = ScraperEngine()
    con = None

    try:

        # ============================================
        # STAGE 1: DOWNLOAD PDFs
        # ============================================
        stage_header("STAGE 1: DOWNLOADING PDFs")

        for stream_code in tqdm(TARGET_STREAMS, desc="Downloading Streams"):
            try:
                logger.info(f"Downloading PDFs for stream: {stream_code}")
                await scraper.run(stream_code)

            except Exception as e:
                logger.error(f"Scraping failed for {stream_code}: {e}")

        await scraper.close()
        logger.info("Stage 1 Complete")

        # ============================================
        # STAGE 2: PROCESS PDFs
        # ============================================
        stage_header("STAGE 2: PROCESSING PDFs")

        for stream_code in tqdm(TARGET_STREAMS, desc="Processing Streams"):
            try:
                logger.info(f"Processing PDFs for stream: {stream_code}")
                pdf_utils.process_stream(stream_code)

            except Exception as e:
                logger.error(f"Processing failed for {stream_code}: {e}")

        logger.info("Stage 2 Complete")

        # ============================================
        # STAGE 3: DATABASE INIT + SYNC
        # ============================================
        stage_header("STAGE 3: DATABASE INITIALIZATION")

        con = db_utils.get_connection()
        db_utils.init_db(con)

        for stream_code in tqdm(TARGET_STREAMS, desc="Syncing Assets"):
            try:
                logger.info(f"Syncing assets to DB for stream: {stream_code}")
                pdf_utils.sync_assets_to_db(con, stream_code)

            except Exception as e:
                logger.error(f"Asset sync failed for {stream_code}: {e}")

        logger.info("Stage 3 Complete")

        # ============================================
        # STAGE 4: CLASSIFICATION PROMPTS
        # ============================================
        stage_header("STAGE 4: GENERATING CLASSIFICATION PROMPTS")

        for stream in tqdm(TARGET_STREAMS, desc="Classification Prompts"):
            try:
                logger.info(f"Generating classification prompts for {stream}")
                prompt_utils.generate_classification_prompts(
                    con,
                    stream,
                    batch_size=CLASSIFICATION_BATCH_SIZE,
                )

            except Exception as e:
                logger.error(f"Prompt generation failed for {stream}: {e}")

        logger.info("Stage 4 Complete")

        # ============================================
        # STAGE 5: PROCESS CLASSIFICATION PROMPTS
        # ============================================
        stage_header("STAGE 5: PROCESSING CLASSIFICATION PROMPTS")

        logger.info(
            f"Processing classification prompts with LLM (limit={TEST_PROMPT_LIMIT})"
        )

        await knowledge_utils.process_classification_prompts(
            limit=TEST_PROMPT_LIMIT
        )

        logger.info("Parsing classification responses")
        knowledge_utils.parse_classification_responses(con)

        logger.info("Stage 5 Complete")

        # ============================================
        # STAGE 6: THEORY PROMPTS
        # ============================================
        stage_header("STAGE 6: GENERATING THEORY PROMPTS")

        for stream in tqdm(TARGET_STREAMS, desc="Theory Prompts"):
            try:
                logger.info(f"Generating theory prompts for {stream}")
                prompt_utils.generate_theory_prompts(con, stream)

            except Exception as e:
                logger.error(f"Theory prompt generation failed for {stream}: {e}")

        logger.info("Stage 6 Complete")

        # ============================================
        # STAGE 7: PROCESS THEORY PROMPTS
        # ============================================
        stage_header("STAGE 7: PROCESSING THEORY PROMPTS")

        logger.info("Processing theory prompts with LLM")
        await knowledge_utils.process_theory_prompts(con)

        logger.info("Stage 7 Complete")

        # ============================================
        # STAGE 8: GENERATE MANIFEST
        # ============================================
        stage_header("STAGE 8: GENERATING MANIFEST")

        for stream in tqdm(TARGET_STREAMS, desc="Generating Manifests"):
            try:
                knowledge_utils.generate_manifest(con, stream)

            except Exception as e:
                logger.error(f"Manifest generation failed for {stream}: {e}")

        logger.info("Stage 8 Complete")

    except Exception as e:
        logger.error("Pipeline failed", exc_info=True)
        raise

    finally:

        # Close DB safely
        if con:
            con.close()

        # Ensure scraper closes
        if scraper and scraper.browser:
            await scraper.close()

    logger.info("=" * 60)
    logger.info("ASSET GENERATOR PIPELINE COMPLETE")
    logger.info("=" * 60)


# -------------------------
# Program Entry
# -------------------------
if __name__ == "__main__":

    try:
        asyncio.run(main())

    except KeyboardInterrupt:
        logger.info("Gracefully stopping pipeline...")

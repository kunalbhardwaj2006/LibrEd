import asyncio
import logging
import sys
import os
from tqdm import tqdm

from generator.src.config import TARGET_STREAMS, GATE_ASSETS_DIR, CLASSIFICATION_BATCH_SIZE, TEST_PROMPT_LIMIT
from generator.src.scraper_engine import ScraperEngine
from generator.src.model_manager import ensure_model_available

# Functional Modules
import generator.src.pdf_utils as pdf_utils
import generator.src.prompt_utils as prompt_utils
import generator.src.knowledge_utils as knowledge_utils
import generator.src.db_utils as db_utils

# Configure Logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)

logger = logging.getLogger("AssetGenerator")


async def main():
    logger.info("Starting Asset Generator - Sequential Pipeline (Functional)")

    # Ensure model is available
    if not ensure_model_available():
        logger.error("Model availability check failed. Exiting pipeline.")
        sys.exit(1)

    # Ensure directories exist
    os.makedirs(GATE_ASSETS_DIR, exist_ok=True)

    scraper = ScraperEngine()
    con = None

    try:

        # ==========================
        # STAGE 1: DOWNLOAD ALL PDFs
        # ==========================
        logger.info("=" * 60)
        logger.info("STAGE 1: DOWNLOADING ALL PDFs FOR ALL STREAMS")
        logger.info("=" * 60)

        for stream_code in tqdm(TARGET_STREAMS, desc="Downloading Streams"):
            logger.info(f"Downloading PDFs for stream: {stream_code}")
            try:
                await scraper.run(stream_code)
            except Exception as e:
                logger.error(f"Scraping failed for {stream_code}: {e}")

        await scraper.close()
        logger.info("Stage 1 Complete: All PDFs downloaded")

        # ==========================
        # STAGE 2: PROCESS ALL PDFs
        # ==========================
        logger.info("=" * 60)
        logger.info("STAGE 2: PROCESSING ALL PDFs TO GENERATE ASSETS")
        logger.info("=" * 60)

        for stream_code in tqdm(TARGET_STREAMS, desc="Processing PDFs"):
            logger.info(f"Processing PDFs for stream: {stream_code}")
            try:
                pdf_utils.process_stream(stream_code)
            except Exception as e:
                logger.error(f"Processing failed for {stream_code}: {e}")

        logger.info("Stage 2 Complete: All assets generated")

        # =====================================
        # STAGE 3: DATABASE INITIALIZATION
        # =====================================
        logger.info("=" * 60)
        logger.info("STAGE 3: INITIALIZING DATABASE AND SYNCING ASSETS")
        logger.info("=" * 60)

        con = db_utils.get_connection()
        db_utils.init_db(con)

        for stream_code in tqdm(TARGET_STREAMS, desc="Syncing Assets to DB"):
            logger.info(f"Syncing assets to DB for stream: {stream_code}")
            try:
                pdf_utils.sync_assets_to_db(con, stream_code)
            except Exception as e:
                logger.error(f"Asset sync failed for {stream_code}: {e}")

        logger.info("Stage 3 Complete: Database populated")

        # =====================================
        # STAGE 4: GENERATE CLASSIFICATION PROMPTS
        # =====================================
        logger.info("=" * 60)
        logger.info("STAGE 4: GENERATING CLASSIFICATION PROMPTS")
        logger.info("=" * 60)

        for stream in tqdm(TARGET_STREAMS, desc="Generating Classification Prompts"):
            logger.info(f"Generating classification prompts for {stream}")
            try:
                prompt_utils.generate_classification_prompts(
                    con,
                    stream,
                    batch_size=CLASSIFICATION_BATCH_SIZE
                )
            except Exception as e:
                logger.error(f"Prompt generation failed for {stream}: {e}")

        logger.info("Stage 4 Complete")

        # =====================================
        # STAGE 5: PROCESS CLASSIFICATION PROMPTS
        # =====================================
        logger.info("=" * 60)
        logger.info("STAGE 5: PROCESSING CLASSIFICATION PROMPTS")
        logger.info("=" * 60)

        logger.info(f"Processing classification prompts with LLM (limit={TEST_PROMPT_LIMIT})")

        await knowledge_utils.process_classification_prompts(
            limit=TEST_PROMPT_LIMIT
        )

        logger.info("Parsing classification responses")
        knowledge_utils.parse_classification_responses(con)

        logger.info("Stage 5 Complete")

        # =====================================
        # STAGE 6: GENERATE THEORY PROMPTS
        # =====================================
        logger.info("=" * 60)
        logger.info("STAGE 6: GENERATING THEORY PROMPTS")
        logger.info("=" * 60)

        for stream in tqdm(TARGET_STREAMS, desc="Generating Theory Prompts"):
            logger.info(f"Generating theory prompts for {stream}")
            try:
                prompt_utils.generate_theory_prompts(con, stream)
            except Exception as e:
                logger.error(f"Theory prompt generation failed for {stream}: {e}")

        logger.info("Stage 6 Complete")

        # =====================================
        # STAGE 7: PROCESS THEORY PROMPTS
        # =====================================
        logger.info("=" * 60)
        logger.info("STAGE 7: PROCESSING THEORY PROMPTS")
        logger.info("=" * 60)

        logger.info("Processing theory prompts with LLM")

        await knowledge_utils.process_theory_prompts(con)

        # =====================================
        # STAGE 8: GENERATE MANIFEST
        # =====================================
        logger.info("=" * 60)
        logger.info("STAGE 8: GENERATING MANIFEST FILES")
        logger.info("=" * 60)

        for stream in tqdm(TARGET_STREAMS, desc="Generating Manifests"):
            try:
                knowledge_utils.generate_manifest(con, stream)
            except Exception as e:
                logger.error(f"Manifest generation failed for {stream}: {e}")

        logger.info("Stage 7 & 8 Complete")

    except Exception as e:
        logger.error(f"Pipeline failed: {e}", exc_info=True)
        raise

    finally:

        if con:
            con.close()

        if scraper and scraper.browser:
            await scraper.close()

    logger.info("=" * 60)
    logger.info("ASSET GENERATOR PIPELINE COMPLETE")
    logger.info("=" * 60)


if __name__ == "__main__":

    try:
        asyncio.run(main())

    except KeyboardInterrupt:
        logger.info("Gracefully stopping pipeline...")

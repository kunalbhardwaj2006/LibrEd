import asyncio
import logging
import sys
import os
import argparse

from generator.src.config import TARGET_STREAMS, GATE_ASSETS_DIR, CLASSIFICATION_BATCH_SIZE, TEST_PROMPT_LIMIT
from generator.src.scraper_engine import ScraperEngine
from generator.src.model_manager import ensure_model_available

# Functional Modules
import generator.src.pdf_utils as pdf_utils
import generator.src.prompt_utils as prompt_utils
import generator.src.knowledge_utils as knowledge_utils
import generator.src.db_utils as db_utils

# Metrics
from .metrics import PipelineMetrics

# -------------------------------
# CLI ARGUMENTS (DEBUG MODE)
# -------------------------------
parser = argparse.ArgumentParser(description="Asset Generator Pipeline")
parser.add_argument("--debug", action="store_true", help="Enable debug mode with detailed pipeline logs")
args = parser.parse_args()

DEBUG = args.debug

# -------------------------------
# LOGGING CONFIG
# -------------------------------
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)

logger = logging.getLogger("AssetGenerator")

# -------------------------------
# DEBUG HELPERS
# -------------------------------
def debug_log(message):
    if DEBUG:
        logger.info(f"[DEBUG] {message}")

def print_pipeline_flow():
    logger.info("\n🔍 DEBUG MODE ENABLED")
    logger.info("Pipeline Flow:")
    logger.info("PDF → Extraction → DB Sync → Classification → Theory → Manifest\n")

# -------------------------------
# MAIN PIPELINE
# -------------------------------
async def main():
    logger.info("Starting Asset Generator")

    if DEBUG:
        print_pipeline_flow()

    metrics = PipelineMetrics()
    scraper = ScraperEngine()

    try:
        # ALL STAGES (ONLY ONCE)

    except Exception as e:
        ...

    finally:
        ...

    # FINAL LOGS
    logger.info("PIPELINE COMPLETE")

    # ✅ ONLY HERE
    if DEBUG:
        metrics.report()
    
    try:
        # ===== STAGE 1: DOWNLOAD PDFs =====
        stage = "PDF Download Stage"
        metrics.start(stage)
        debug_log(f"➡️ Starting: {stage}")

        for stream_code in TARGET_STREAMS:
            logger.info(f"Downloading PDFs for stream: {stream_code}")
            try:
                await scraper.run(stream_code)
            except Exception as e:
                logger.error(f"Scraping failed for {stream_code}: {e}")

        await scraper.close()
        metrics.end(stage)
        debug_log(f"✅ Completed: {stage}")

        # ===== STAGE 2: PROCESS PDFs =====
        stage = "PDF Processing"
        metrics.start(stage)
        debug_log(f"➡️ Starting: {stage}")

        for stream_code in TARGET_STREAMS:
            logger.info(f"Processing PDFs for stream: {stream_code}")
            try:
                pdf_utils.process_stream(stream_code)
            except Exception as e:
                logger.error(f"Processing failed for {stream_code}: {e}")

        metrics.end(stage)
        debug_log(f"✅ Completed: {stage}")

        # ===== STAGE 3: DB INIT + SYNC =====
        stage = "Database Sync"
        metrics.start(stage)
        debug_log(f"➡️ Starting: {stage}")

        con = db_utils.get_connection()
        db_utils.init_db(con)

        for stream_code in TARGET_STREAMS:
            logger.info(f"Syncing assets to DB for stream: {stream_code}")
            try:
                pdf_utils.sync_assets_to_db(con, stream_code)
            except Exception as e:
                logger.error(f"Asset sync failed for {stream_code}: {e}")

        metrics.end(stage)
        debug_log(f"✅ Completed: {stage}")

        # ===== STAGE 4: CLASSIFICATION PROMPTS =====
        stage = "Classification Prompt Generation"
        metrics.start(stage)
        debug_log(f"➡️ Starting: {stage}")

        for stream in TARGET_STREAMS:
            prompt_utils.generate_classification_prompts(
                con, stream, batch_size=CLASSIFICATION_BATCH_SIZE
            )

        metrics.end(stage)
        debug_log(f"✅ Completed: {stage}")

        # ===== STAGE 5: CLASSIFICATION (LLM) =====
        stage = "Classification Processing"
        metrics.start(stage)
        debug_log(f"➡️ Starting: {stage}")

        await knowledge_utils.process_classification_prompts(limit=TEST_PROMPT_LIMIT)
        knowledge_utils.parse_classification_responses(con)

        metrics.end(stage)
        debug_log(f"✅ Completed: {stage}")

        # ===== STAGE 6: THEORY PROMPTS =====
        stage = "Theory Prompt Generation"
        metrics.start(stage)
        debug_log(f"➡️ Starting: {stage}")

        for stream in TARGET_STREAMS:
            prompt_utils.generate_theory_prompts(con, stream)

        metrics.end(stage)
        debug_log(f"✅ Completed: {stage}")

        # ===== STAGE 7: THEORY PROCESSING =====
        stage = "Theory Processing"
        metrics.start(stage)
        debug_log(f"➡️ Starting: {stage}")

        await knowledge_utils.process_theory_prompts(con)

        metrics.end(stage)
        debug_log(f"✅ Completed: {stage}")

        # ===== STAGE 8: MANIFEST =====
        stage = "Manifest Generation"
        metrics.start(stage)
        debug_log(f"➡️ Starting: {stage}")

        for stream in TARGET_STREAMS:
            knowledge_utils.generate_manifest(con, stream)

        con.close()
        metrics.end(stage)
        debug_log(f"✅ Completed: {stage}")

    except Exception as e:
        logger.error(f"Pipeline failed: {e}", exc_info=True)
        raise
    finally:
        if scraper.browser:
            await scraper.close()

    # ===== FINAL OUTPUT =====
    logger.info("=" * 60)
    logger.info("ASSET GENERATOR PIPELINE COMPLETE")
    logger.info("=" * 60)


# -------------------------------
# ENTRY POINT
# -------------------------------
if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Gracefully Stopping...")

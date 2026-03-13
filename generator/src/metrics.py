import time
import logging


class PipelineMetrics:
    def __init__(self):
        self.stages = {}

    def start(self, stage):
        self.stages[stage] = {"start": time.time()}

    def end(self, stage):
        if stage in self.stages:
            self.stages[stage]["end"] = time.time()

    def report(self):
        logging.info("Pipeline Performance Metrics")

        for stage, data in self.stages.items():
            duration = data["end"] - data["start"]
            logging.info(f"{stage} completed in {duration:.2f} seconds")

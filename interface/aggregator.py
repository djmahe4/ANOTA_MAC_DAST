import datetime
import uuid

class TelemetryAggregator:
    """
    Consolidates telemetry from various sources into a unified stream.
    """
    def aggregate(self, source, data):
        """
        Wraps raw runner output into a unified schema.
        """
        aggregated = {
            "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat(),
            "trace_id": str(uuid.uuid4()),
            "source": source,
            "coverage": {},
            "state": {},
            "events": []
        }
        
        if source == "php":
            # PHPRunner returns {type, coverage, state}
            aggregated["coverage"] = data.get("coverage", {})
            aggregated["state"] = data.get("state", {})
        elif source == "cpp":
            # CPPHarness returns list of event dicts
            aggregated["events"] = data
            
        return aggregated

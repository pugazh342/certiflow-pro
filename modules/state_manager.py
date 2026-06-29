# modules/state_manager.py
import json
from datetime import datetime
import pandas as pd
from typing import Dict, List
import config

class StateManager:
    def __init__(self):
        self.checkpoint_path = config.CHECKPOINT_FILE

    def initialize_job(self, df: pd.DataFrame) -> Dict:
        manifest = {}
        for _, row in df.iterrows():
            rec_id = str(row["_record_id"])
            manifest[rec_id] = {
                "record": row.to_dict(),
                "status": "PENDING",
                "pdf_path": "",
                "error": "",
                "updated_at": datetime.now().isoformat()
            }
        self.save_manifest(manifest)
        return manifest

    def save_manifest(self, manifest: Dict) -> None:
        with open(self.checkpoint_path, "w", encoding="utf-8") as f:
            json.dump(manifest, f, indent=2)

    def load_manifest(self) -> Dict:
        if not self.checkpoint_path.exists():
            return {}
        try:
            with open(self.checkpoint_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {}

    def update_record(self, manifest: Dict, record_id: str, status: str, pdf_path: str = "", error: str = "") -> Dict:
        if record_id in manifest:
            manifest[record_id]["status"] = status
            manifest[record_id]["updated_at"] = datetime.now().isoformat()
            if pdf_path:
                manifest[record_id]["pdf_path"] = pdf_path
            if error:
                manifest[record_id]["error"] = error
            self.save_manifest(manifest)
        return manifest

    def get_resumable_records(self, manifest: Dict) -> List[Dict]:
        """Returns records that have NOT successfully dispatched."""
        resumable = []
        for rec_id, data in manifest.items():
            if data["status"] != "SENT":
                resumable.append(data["record"])
        return resumable

    def export_audit_log(self, manifest: Dict) -> str:
        rows = []
        for rec_id, meta in manifest.items():
            row = {**meta["record"]}
            row.update({
                "Final_Status": meta["status"],
                "PDF_File_Path": meta["pdf_path"],
                "Failure_Reason": meta["error"],
                "Last_Updated": meta["updated_at"]
            })
            rows.append(row)
            
        df = pd.DataFrame(rows)
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        export_path = config.AUDIT_DIR / f"audit_report_{ts}.csv"
        df.to_csv(export_path, index=False)
        return str(export_path)
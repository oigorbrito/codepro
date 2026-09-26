
from __future__ import annotations

import json
import os
from pathlib import Path
import shutil
import sys

from swebench.harness.run_evaluation import main
from swebench.harness.utils import load_swebench_dataset
from swebench.task.checks import expected_image

dataset, split, instance_id, predictions_path, run_id, work_dir, normalized_report = sys.argv[1:]
work = Path(work_dir)
work.mkdir(parents=True, exist_ok=True)
os.chdir(work)

rows = load_swebench_dataset(dataset, split, [instance_id])
if len(rows) != 1:
    raise RuntimeError(f"expected exactly one dataset row for {instance_id}, found {len(rows)}")
instance = dict(rows[0])
derived_image = expected_image(instance_id)
observed_image = instance.get("image")
if observed_image not in (None, derived_image):
    raise RuntimeError(
        f"dataset image mismatch for {instance_id}: observed={observed_image!r} expected={derived_image!r}"
    )
instance["image"] = derived_image
harness_dataset = work / "harness-instance.json"
harness_dataset.write_text(json.dumps([instance], ensure_ascii=False) + "\n", encoding="utf-8")

effective_predictions = predictions_path
if predictions_path == "gold":
    effective_predictions = "gold"

report = main(
    dataset_name=str(harness_dataset),
    split=split,
    instance_ids=[instance_id],
    predictions_path=effective_predictions,
    max_workers=1,
    open_file_limit=4096,
    run_id=run_id,
    timeout=1800,
    rewrite_reports=False,
    modal=False,
)

report_path = Path(report).resolve()
normalized = Path(normalized_report)
normalized.parent.mkdir(parents=True, exist_ok=True)
shutil.copyfile(report_path, normalized)
print("CODEPRO_RESULT=" + json.dumps({"report": str(report_path), "normalized_report": str(normalized)}))

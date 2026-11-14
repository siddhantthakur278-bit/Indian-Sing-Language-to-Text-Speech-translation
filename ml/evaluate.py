"""
Model Evaluation and Metrics Module
Computes Top-1, Top-5 accuracy, per-class Precision/Recall/F1, Confusion Matrix,
and inference latency benchmarks for the ISL model.
"""

import os
import time
import json
import logging
import argparse
import numpy as np
import matplotlib.pyplot as plt
from sklearn.metrics import classification_report, confusion_matrix

os.environ["TF_CPP_MIN_LOG_LEVEL"] = "2"
import tensorflow as tf
from train import load_dataset

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)


def evaluate_model(model_path: str, data_dir: str, classes_path: str, output_dir: str = "docs"):
    """Runs rigorous evaluation on the specified test set with missing-file safety."""
    if not os.path.exists(classes_path):
        logger.error(f"Evaluation failed: classes file '{classes_path}' does not exist.")
        return

    if not os.path.exists(model_path):
        logger.error(f"Evaluation failed: model file '{model_path}' does not exist.")
        return

    if not os.path.exists(data_dir):
        logger.error(f"Evaluation failed: data directory '{data_dir}' does not exist.")
        return

    os.makedirs(output_dir, exist_ok=True)

    with open(classes_path, "r") as f:
        meta = json.load(f)
    classes = meta["classes"]

    logger.info(f"Loading model from {model_path}...")
    model = tf.keras.models.load_model(model_path)

    logger.info(f"Loading evaluation data from {data_dir}...")
    X, y_true, _ = load_dataset(data_dir, classes_path)

    logger.info(f"Evaluating {len(X)} sequences...")

    # Benchmark Latency
    latencies = []
    # Warmup
    _ = model.predict(X[:1], verbose=0)

    for i in range(min(50, len(X))):
        start = time.perf_counter()
        _ = model.predict(X[i:i+1], verbose=0)
        latencies.append((time.perf_counter() - start) * 1000.0)

    mean_latency = np.mean(latencies)
    p95_latency = np.percentile(latencies, 95)
    logger.info(f"Inference Latency: Mean = {mean_latency:.2f} ms, 95th Percentile = {p95_latency:.2f} ms")

    # Full predictions
    probs = model.predict(X, batch_size=32, verbose=0)
    y_pred = np.argmax(probs, axis=1)

    # Top-1 Accuracy
    top1_acc = np.mean(y_pred == y_true) * 100.0

    # Top-5 Accuracy
    top5_correct = 0
    for idx, true_cls in enumerate(y_true):
        top5_preds = np.argsort(probs[idx])[-5:]
        if true_cls in top5_preds:
            top5_correct += 1
    top5_acc = (top5_correct / len(y_true)) * 100.0

    logger.info("==========================================")
    logger.info(f"Top-1 Accuracy : {top1_acc:.2f}%")
    logger.info(f"Top-5 Accuracy : {top5_acc:.2f}%")
    logger.info("==========================================")

    # Classification Report
    unique_present_classes = sorted(list(set(y_true) | set(y_pred)))
    target_names = [classes[i] for i in unique_present_classes]
    report_text = classification_report(y_true, y_pred, labels=unique_present_classes, target_names=target_names, zero_division=0)
    report_dict = classification_report(y_true, y_pred, labels=unique_present_classes, target_names=target_names, output_dict=True, zero_division=0)
    logger.info("\n" + report_text)

    # IDLE vs Non-IDLE breakdown (Contract 7.8)
    idle_idx = classes.index("IDLE") if "IDLE" in classes else -1
    idle_acc = 0.0
    idle_count = 0
    non_idle_acc = 0.0
    non_idle_count = 0
    false_trigger_rate = 0.0

    if idle_idx != -1:
        idle_mask = (y_true == idle_idx)
        idle_count = int(np.sum(idle_mask))
        if idle_count > 0:
            idle_correct = int(np.sum(y_pred[idle_mask] == idle_idx))
            idle_acc = (idle_correct / idle_count) * 100.0
            false_trigger_rate = ((idle_count - idle_correct) / idle_count) * 100.0

        non_idle_mask = ~idle_mask
        non_idle_count = int(np.sum(non_idle_mask))
        if non_idle_count > 0:
            non_idle_correct = int(np.sum(y_pred[non_idle_mask] == y_true[non_idle_mask]))
            non_idle_acc = (non_idle_correct / non_idle_count) * 100.0

        logger.info(f"IDLE Accuracy          : {idle_acc:.2f}% ({idle_count} samples)")
        logger.info(f"IDLE False Trigger Rate: {false_trigger_rate:.2f}%")
        logger.info(f"Non-IDLE Accuracy      : {non_idle_acc:.2f}% ({non_idle_count} samples)")

    # Identify 5 worst-performing classes by F1-score
    class_f1_scores = []
    for cls_name in target_names:
        if cls_name in report_dict:
            class_f1_scores.append((cls_name, report_dict[cls_name]["f1-score"], report_dict[cls_name]["support"]))
    class_f1_scores.sort(key=lambda x: x[1])
    worst_classes = class_f1_scores[:5]

    # Save Confusion Matrix Plot
    cm = confusion_matrix(y_true, y_pred, labels=unique_present_classes)
    plt.figure(figsize=(12, 10))
    plt.imshow(cm, interpolation='nearest', cmap=plt.cm.Blues)
    plt.title("ISL Model Confusion Matrix", fontsize=14)
    plt.colorbar()
    tick_marks = np.arange(len(target_names))
    plt.xticks(tick_marks, target_names, rotation=90, fontsize=8)
    plt.yticks(tick_marks, target_names, fontsize=8)
    plt.ylabel("True Class", fontsize=11)
    plt.xlabel("Predicted Class", fontsize=11)
    plt.tight_layout()

    cm_path = os.path.join(output_dir, "confusion_matrix.png")
    plt.savefig(cm_path, dpi=200)
    plt.close()
    logger.info(f"Saved confusion matrix plot to {cm_path}")

    # Generate Structured Markdown Evaluation Report (Contract 7.8)
    report_md_path = os.path.join(output_dir, "evaluation_report.md")
    with open(report_md_path, "w", encoding="utf-8") as f:
        f.write("# ISL Sign Recognition Model Evaluation Report\n\n")
        f.write(f"- **Model Checkpoint**: `{model_path}`\n")
        f.write(f"- **Evaluated Samples**: {len(X)} sequences across {len(target_names)} active classes\n")
        f.write(f"- **Top-1 Accuracy**: {top1_acc:.2f}%\n")
        f.write(f"- **Top-5 Accuracy**: {top5_acc:.2f}%\n")
        f.write(f"- **Mean CPU Latency**: {mean_latency:.2f} ms\n")
        f.write(f"- **95th Percentile Latency**: {p95_latency:.2f} ms\n\n")
        f.write("## IDLE & False Trigger Analysis\n\n")
        f.write(f"- **IDLE Class Samples**: {idle_count}\n")
        f.write(f"- **IDLE Recognition Accuracy**: {idle_acc:.2f}%\n")
        f.write(f"- **False Trigger Rate on IDLE**: {false_trigger_rate:.2f}%\n")
        f.write(f"- **Active Gesture Accuracy (Non-IDLE)**: {non_idle_acc:.2f}%\n\n")
        f.write("## Lowest Performing Classes (Bottom 5 by F1-Score)\n\n")
        f.write("| Rank | Class Name | F1-Score | Support |\n")
        f.write("|---|---|---|---|\n")
        for rank, (cls_name, f1, sup) in enumerate(worst_classes, start=1):
            f.write(f"| {rank} | `{cls_name}` | {f1:.3f} | {int(sup)} |\n")
        f.write("\n## Confusion Matrix\n\n")
        f.write("![Confusion Matrix](confusion_matrix.png)\n")

    logger.info(f"Saved structured evaluation report to {report_md_path}")

    # Save summary JSON for programmatic verification
    summary_json_path = os.path.join(output_dir, "evaluation_summary.json")
    summary_data = {
        "model_path": model_path,
        "num_samples": len(X),
        "top1_accuracy": top1_acc,
        "top5_accuracy": top5_acc,
        "mean_latency_ms": mean_latency,
        "p95_latency_ms": p95_latency,
        "idle_accuracy": idle_acc,
        "idle_false_trigger_rate": false_trigger_rate,
        "worst_classes": [{"class": c, "f1": f1, "support": int(s)} for c, f1, s in worst_classes],
    }
    with open(summary_json_path, "w", encoding="utf-8") as f:
        json.dump(summary_data, f, indent=2)
    logger.info(f"Saved evaluation metrics JSON to {summary_json_path}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Evaluate ISL model")
    parser.add_argument("--model", type=str, default="isl_model.keras", help="Path to trained model")
    parser.add_argument("--data", type=str, default="data/processed", help="Path to processed sequences")
    parser.add_argument("--classes", type=str, default="data/classes.json", help="Path to classes.json")
    parser.add_argument("--output", type=str, default="docs", help="Directory for report outputs")
    args = parser.parse_args()

    evaluate_model(args.model, args.data, args.classes, output_dir=args.output)

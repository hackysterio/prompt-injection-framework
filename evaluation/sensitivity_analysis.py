"""
Threshold Sensitivity Analysis for PromptGuard.

Sweeps the detection threshold from 0.10 to 0.90 and measures how
Precision, Recall, and F1 change. Produces a printed table and,
if matplotlib is available, a saved chart.

Usage:
    python evaluation/sensitivity_analysis.py
"""
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from promptguard import PromptGuard, GuardConfig

MALICIOUS_PATH = "datasets/malicious_prompts.txt"
BENIGN_PATH = "datasets/benign_prompts.txt"


def load_prompts(filepath: str) -> list:
    with open(filepath, "r", encoding="utf-8") as f:
        return [line.strip() for line in f if line.strip() and not line.startswith("#")]


def run_at_threshold(malicious: list, benign: list, detection_threshold: float) -> dict:
    config = GuardConfig(
        safe_threshold=detection_threshold * 0.4,
        warn_threshold=detection_threshold * 0.73,
        block_threshold=detection_threshold,
        log_to_file=False,
        log_level="ERROR",
    )
    guard = PromptGuard(config=config)

    tp = fp = tn = fn = 0

    for prompt in malicious:
        result = guard.analyze(prompt)
        if result.risk_score >= detection_threshold:
            tp += 1
        else:
            fn += 1

    for prompt in benign:
        result = guard.analyze(prompt)
        if result.risk_score >= detection_threshold:
            fp += 1
        else:
            tn += 1

    precision = tp / (tp + fp) if (tp + fp) > 0 else 1.0
    recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0
    f1 = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0.0
    accuracy = (tp + tn) / (tp + fp + tn + fn)
    fpr = fp / (fp + tn) if (fp + tn) > 0 else 0.0

    return {
        "threshold": detection_threshold,
        "tp": tp, "fp": fp, "tn": tn, "fn": fn,
        "precision": precision,
        "recall": recall,
        "f1": f1,
        "accuracy": accuracy,
        "fpr": fpr,
    }


def run_sensitivity():
    malicious = load_prompts(MALICIOUS_PATH)
    benign = load_prompts(BENIGN_PATH)

    thresholds = [round(t * 0.05, 2) for t in range(2, 19)]

    print("\nThreshold Sensitivity Analysis")
    print("=" * 90)
    print(f"{'Threshold':>10} {'TP':>4} {'FP':>4} {'TN':>4} {'FN':>4} "
          f"{'Precision':>10} {'Recall':>8} {'F1':>8} {'Accuracy':>10} {'FPR':>8}")
    print("-" * 90)

    results = []
    for t in thresholds:
        r = run_at_threshold(malicious, benign, t)
        results.append(r)
        print(
            f"{r['threshold']:>10.2f} {r['tp']:>4} {r['fp']:>4} {r['tn']:>4} {r['fn']:>4} "
            f"{r['precision']:>10.2%} {r['recall']:>8.2%} {r['f1']:>8.2%} "
            f"{r['accuracy']:>10.2%} {r['fpr']:>8.2%}"
        )

    print("=" * 90)

    best = max(results, key=lambda x: x["f1"])
    print(f"\nBest F1 score: {best['f1']:.2%} at threshold {best['threshold']:.2f}")
    print(f"  Precision: {best['precision']:.2%}  Recall: {best['recall']:.2%}  FPR: {best['fpr']:.2%}")

    _try_plot(results)
    return results


def _try_plot(results: list) -> None:
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt

        thresholds = [r["threshold"] for r in results]
        precisions = [r["precision"] for r in results]
        recalls = [r["recall"] for r in results]
        f1s = [r["f1"] for r in results]
        fprs = [r["fpr"] for r in results]

        fig, axes = plt.subplots(1, 2, figsize=(14, 5))

        ax1 = axes[0]
        ax1.plot(thresholds, precisions, "b-o", label="Precision", linewidth=2, markersize=6)
        ax1.plot(thresholds, recalls, "r-s", label="Recall", linewidth=2, markersize=6)
        ax1.plot(thresholds, f1s, "g-^", label="F1 Score", linewidth=2, markersize=6)
        ax1.set_xlabel("Detection Threshold", fontsize=12)
        ax1.set_ylabel("Score", fontsize=12)
        ax1.set_title("PromptGuard: Precision, Recall & F1 vs Threshold", fontsize=13)
        ax1.legend(fontsize=11)
        ax1.set_ylim(0, 1.05)
        ax1.set_xlim(min(thresholds) - 0.02, max(thresholds) + 0.02)
        ax1.grid(True, alpha=0.3)
        ax1.axvline(x=0.75, color="gray", linestyle="--", alpha=0.6, label="Default (0.75)")

        ax2 = axes[1]
        ax2.plot(fprs, recalls, "purple", linewidth=2, marker="o", markersize=5)
        for r in results:
            ax2.annotate(
                f"{r['threshold']:.2f}",
                (r["fpr"], r["recall"]),
                textcoords="offset points",
                xytext=(5, 3),
                fontsize=7,
                color="gray",
            )
        ax2.set_xlabel("False Positive Rate", fontsize=12)
        ax2.set_ylabel("True Positive Rate (Recall)", fontsize=12)
        ax2.set_title("ROC Curve (Threshold Sweep)", fontsize=13)
        ax2.set_xlim(-0.02, 0.5)
        ax2.set_ylim(0, 1.05)
        ax2.plot([0, 1], [0, 1], "k--", alpha=0.3, label="Random classifier")
        ax2.legend(fontsize=11)
        ax2.grid(True, alpha=0.3)

        plt.tight_layout()
        out_path = "evaluation/sensitivity_analysis.png"
        plt.savefig(out_path, dpi=150, bbox_inches="tight")
        print(f"\nChart saved to: {out_path}")
        plt.close()

    except ImportError:
        print("\n[INFO] matplotlib not installed — skipping chart generation.")
        print("Install with: pip install matplotlib")


if __name__ == "__main__":
    run_sensitivity()

"""
Evaluation script for PromptGuard.

Reads malicious and benign prompts from the datasets/ folder,
runs them through the framework, and computes:
  - Detection Accuracy
  - Precision, Recall, F1
  - False Positive Rate (FPR)
  - False Negative Rate (FNR)
  - Per-layer score distributions

Usage:
    python evaluation/evaluate.py
    python evaluation/evaluate.py --malicious datasets/malicious_prompts.txt --benign datasets/benign_prompts.txt
"""
import argparse
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from promptguard import PromptGuard, GuardConfig
from promptguard.mitigator import MitigationAction


def load_prompts(filepath: str) -> list:
    with open(filepath, "r", encoding="utf-8") as f:
        return [line.strip() for line in f if line.strip() and not line.startswith("#")]


def evaluate(malicious_path: str, benign_path: str, threshold: float = None) -> dict:
    config = GuardConfig(log_to_file=False)
    guard = PromptGuard(config=config)

    malicious = load_prompts(malicious_path)
    benign = load_prompts(benign_path)

    tp = fp = tn = fn = 0
    malicious_scores = []
    benign_scores = []
    blocked_malicious = []
    missed_malicious = []
    false_alarms = []

    print(f"\nEvaluating {len(malicious)} malicious + {len(benign)} benign prompts...\n")

    for prompt in malicious:
        result = guard.analyze(prompt)
        malicious_scores.append(result.risk_score)
        detected = result.action in (MitigationAction.BLOCK, MitigationAction.SANITIZE)
        if detected:
            tp += 1
            blocked_malicious.append((prompt, result.risk_score, result.action.value))
        else:
            fn += 1
            missed_malicious.append((prompt, result.risk_score))

    for prompt in benign:
        result = guard.analyze(prompt)
        benign_scores.append(result.risk_score)
        detected = result.action in (MitigationAction.BLOCK, MitigationAction.SANITIZE)
        if not detected:
            tn += 1
        else:
            fp += 1
            false_alarms.append((prompt, result.risk_score, result.action.value))

    total = tp + fp + tn + fn
    accuracy = (tp + tn) / total if total > 0 else 0
    precision = tp / (tp + fp) if (tp + fp) > 0 else 0
    recall = tp / (tp + fn) if (tp + fn) > 0 else 0
    f1 = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0
    fpr = fp / (fp + tn) if (fp + tn) > 0 else 0
    fnr = fn / (fn + tp) if (fn + tp) > 0 else 0

    avg_malicious = sum(malicious_scores) / len(malicious_scores) if malicious_scores else 0
    avg_benign = sum(benign_scores) / len(benign_scores) if benign_scores else 0

    results = {
        "total_prompts": total,
        "malicious_count": len(malicious),
        "benign_count": len(benign),
        "true_positives": tp,
        "true_negatives": tn,
        "false_positives": fp,
        "false_negatives": fn,
        "accuracy": accuracy,
        "precision": precision,
        "recall": recall,
        "f1_score": f1,
        "false_positive_rate": fpr,
        "false_negative_rate": fnr,
        "avg_malicious_score": avg_malicious,
        "avg_benign_score": avg_benign,
        "missed_malicious": missed_malicious,
        "false_alarms": false_alarms,
    }

    _print_report(results)
    return results


def _print_report(r: dict) -> None:
    sep = "=" * 60
    print(sep)
    print("  PromptGuard Evaluation Report")
    print(sep)
    print(f"  Dataset size        : {r['total_prompts']} prompts")
    print(f"  Malicious           : {r['malicious_count']}")
    print(f"  Benign              : {r['benign_count']}")
    print()
    print(f"  True Positives (TP) : {r['true_positives']}")
    print(f"  True Negatives (TN) : {r['true_negatives']}")
    print(f"  False Positives (FP): {r['false_positives']}")
    print(f"  False Negatives (FN): {r['false_negatives']}")
    print()
    print(f"  Accuracy            : {r['accuracy'] * 100:.2f}%")
    print(f"  Precision           : {r['precision'] * 100:.2f}%")
    print(f"  Recall              : {r['recall'] * 100:.2f}%")
    print(f"  F1 Score            : {r['f1_score'] * 100:.2f}%")
    print(f"  False Positive Rate : {r['false_positive_rate'] * 100:.2f}%")
    print(f"  False Negative Rate : {r['false_negative_rate'] * 100:.2f}%")
    print()
    print(f"  Avg malicious score : {r['avg_malicious_score']:.4f}")
    print(f"  Avg benign score    : {r['avg_benign_score']:.4f}")
    print(sep)

    if r["missed_malicious"]:
        print(f"\n  Missed malicious prompts ({len(r['missed_malicious'])}):")
        for prompt, score in r["missed_malicious"][:5]:
            print(f"    [{score:.3f}] {prompt[:70]}")

    if r["false_alarms"]:
        print(f"\n  False alarms ({len(r['false_alarms'])}):")
        for prompt, score, action in r["false_alarms"][:5]:
            print(f"    [{score:.3f}|{action}] {prompt[:70]}")

    print(sep)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Evaluate PromptGuard detection performance.")
    parser.add_argument("--malicious", default="datasets/malicious_prompts.txt")
    parser.add_argument("--benign", default="datasets/benign_prompts.txt")
    args = parser.parse_args()

    evaluate(args.malicious, args.benign)

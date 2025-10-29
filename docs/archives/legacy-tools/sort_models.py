#!/usr/bin/env python3
import json
from pathlib import Path
from collections import defaultdict

def sort_and_organize_models(input_file, output_file):
    """Sort models by type and create organized output"""

    # Read the scan results
    with open(input_file, 'r') as f:
        models = json.load(f)

    # Organize by type
    by_type = defaultdict(list)
    for model in models:
        model_type = model.get('type_hint', 'unknown')
        by_type[model_type].append(model)

    # Sort each type's list by path
    for type_name in by_type:
        by_type[type_name].sort(key=lambda x: x['path'])

    # Create organized output
    organized = {
        "summary": {
            "total_models": len(models),
            "by_type": {k: len(v) for k, v in by_type.items()}
        },
        "models_by_type": dict(by_type)
    }

    # Write sorted output
    with open(output_file, 'w') as f:
        json.dump(organized, f, indent=2)

    # Print summary
    print(f"\n=== Model Scan Summary ===")
    print(f"Total models found: {len(models)}\n")
    print("Breakdown by type:")
    for type_name, models_list in sorted(by_type.items(), key=lambda x: len(x[1]), reverse=True):
        print(f"  {type_name}: {len(models_list)}")

    # Print file locations by type
    print(f"\n=== Model Locations by Type ===")
    for type_name in sorted(by_type.keys()):
        print(f"\n{type_name.upper()} ({len(by_type[type_name])} files):")
        for model in by_type[type_name][:5]:  # Show first 5 of each type
            path = Path(model['path'])
            size_mb = model.get('size_bytes', 0) / (1024 * 1024)
            print(f"  - {path.name} ({size_mb:.1f} MB)")
            print(f"    {path.parent}")
        if len(by_type[type_name]) > 5:
            print(f"  ... and {len(by_type[type_name]) - 5} more")

    print(f"\nDetailed sorted output saved to: {output_file}")

if __name__ == "__main__":
    sort_and_organize_models(
        "scan_results_sorted.json",
        "models_organized.json"
    )

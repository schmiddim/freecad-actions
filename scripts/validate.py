"""Validate metadata and profile YAML files against their JSON schemas."""

import json
import os
import sys
import glob

import yaml
from jsonschema import validate, ValidationError


def load_schema(schema_path):
    """Load a JSON schema file."""
    with open(schema_path) as f:
        return json.load(f)


def validate_file(yaml_path, schema, schema_name):
    """Validate a single YAML file against a schema. Returns True if valid."""
    try:
        with open(yaml_path) as f:
            data = yaml.safe_load(f)
    except yaml.YAMLError as e:
        print(f"  FAIL: {yaml_path} - YAML parse error: {e}")
        return False

    if data is None:
        print(f"  FAIL: {yaml_path} - File is empty")
        return False

    try:
        validate(instance=data, schema=schema)
        print(f"  OK:   {yaml_path}")
        return True
    except ValidationError as e:
        print(f"  FAIL: {yaml_path} - {e.message}")
        return False


def main():
    # Load gallery config to find metadata_dir
    config_path = "gallery.yaml"
    if os.path.exists(config_path):
        with open(config_path) as f:
            config = yaml.safe_load(f) or {}
    else:
        config = {}

    metadata_dir = config.get("metadata_dir", "metadata")
    errors = 0
    checked = 0

    # Validate profile.yaml
    profile_schema_path = "schemas/profile.schema.json"
    profile_path = "profile.yaml"
    if os.path.exists(profile_path) and os.path.exists(profile_schema_path):
        print("Validating profile:")
        profile_schema = load_schema(profile_schema_path)
        checked += 1
        if not validate_file(profile_path, profile_schema, "profile"):
            errors += 1
    else:
        print(f"Skipping profile validation (file not found)")

    # Validate metadata files
    meta_schema_path = "schemas/meta.schema.json"
    if os.path.exists(meta_schema_path):
        meta_schema = load_schema(meta_schema_path)
        meta_files = glob.glob(os.path.join(metadata_dir, "*.yaml"))
        meta_files += glob.glob(os.path.join(metadata_dir, "*.yml"))

        if meta_files:
            print(f"\nValidating metadata ({len(meta_files)} files):")
            for meta_file in sorted(meta_files):
                checked += 1
                if not validate_file(meta_file, meta_schema, "metadata"):
                    errors += 1
        else:
            print(f"No metadata files found in '{metadata_dir}/'")
    else:
        print(f"Schema not found: {meta_schema_path}")
        errors += 1

    # Summary
    print(f"\n{'=' * 40}")
    print(f"Checked: {checked}, Passed: {checked - errors}, Failed: {errors}")

    if errors > 0:
        sys.exit(1)
    else:
        print("All validations passed.")


if __name__ == "__main__":
    main()

import os
import sys
import json

""" This script is used to assert that the metric value in the file at file_path is greater than or equal to the expected value.

    Usage: python assert.py <file_path> <expected_value>
"""
def assert_metric(file_path:str, expected_value: str) -> bool:
    result = json.load(open(file_path))
    metric_value = result['accuracy'] 

    return float(metric_value) >= float(expected_value)
    
def main():
    cwd = os.getcwd()
    path = os.path.join(cwd,'promptflow/llmops-helper',sys.argv[1])
    expected_value = sys.argv[2]

    pass_bool = assert_metric(path, expected_value)
    
    return pass_bool

if __name__ == "__main__":
    result = main()
    print(bool(result))
    
import os
import sys

def main():
    cwd = os.getcwd()
    path = os.path.join(cwd,'promptflow/llmops-helper',sys.argv[1])
    with open(path, 'r') as f:
        output = f.read()

    start = output.find('"name": "') + len('"name": "')
    end = output.find('"', start)

    name = output[start:end]
    return name

if __name__ == "__main__":
    run_name = main()
    print(run_name)
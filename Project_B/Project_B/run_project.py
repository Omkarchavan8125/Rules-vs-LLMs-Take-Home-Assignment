from pathlib import Path
from src.pipeline import run
if __name__ == '__main__':
    run(Path(__file__).parent/'data'/'export.csv', Path(__file__).parent)
    print('Project B completed: profile.json, benchmark.csv, RESULTS_B.md, DECISION_MATRIX.md, AI_USAGE.md')

import sys, subprocess, json, os
from pathlib import Path
if sys.version_info < (3,10):
    raise SystemExit("Python 3.10+ required")
ROOT=Path(__file__).resolve().parent
subprocess.run([sys.executable,"-m","pip","install","-r",str(ROOT/"requirements.txt")],check=True)
subprocess.run([sys.executable,"-m","pytest","-q",str(ROOT/"tests")],check=True)
subprocess.run([sys.executable,str(ROOT/"tests"/"generate_cases.py")],check=True,cwd=ROOT)
from src.tax_engine import calculate
salaries=[0,250000,300000,500000,700000,1000000,1200000,1500000,2000000,2500000,5000000,10000000]
results={"python_version":sys.version.split()[0],"test_command":"python run_all.py","cases":[{"salary":x,"FY2024-25":calculate({"salary":x}, "2024-25"),"FY2025-26":calculate({"salary":x}, "2025-26")} for x in salaries]}
out=ROOT/"results"; out.mkdir(exist_ok=True)
(out/"reproduced_results.json").write_text(json.dumps(results,indent=2),encoding="utf-8")
print("Reproduced",len(salaries),"salary scenarios -> results/reproduced_results.json")

import argparse,json
from src.tax_engine import calculate
p=argparse.ArgumentParser();p.add_argument('--income',type=int,required=True);p.add_argument('--fy',choices=['2024-25','2025-26'],default='2024-25');a=p.parse_args();print(json.dumps(calculate({'salary':a.income},a.fy),indent=2))

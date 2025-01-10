import sys
sys.path.remove("/home/runner/work/tradeflow/tradeflow")
import tradeflow
import importlib.metadata


for s in sys.path:
    print(f"\n==={s}")
print(f"__file__: {tradeflow.__file__}")
print(f"VERSION: {importlib.metadata.version('tradeflow')}")
# /home/runner/work/tradeflow/tradeflow/tradeflow/__init__.py

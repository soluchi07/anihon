import sys
from pathlib import Path

# Ensure this lambda's source directory is at the front of sys.path
# and clear any cached 'handler' / 'algorithm' modules from previous lambdas.
_lambda_src = str(Path(__file__).parent.parent)
if _lambda_src in sys.path:
    sys.path.remove(_lambda_src)
sys.path.insert(0, _lambda_src)
sys.modules.pop("handler", None)
sys.modules.pop("algorithm", None)

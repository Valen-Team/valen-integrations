"""Copy the single maintained workflow protocol into independently distributable packages."""
from pathlib import Path
import argparse
root = Path(__file__).resolve().parents[1]
source = '# Generated from shared/protocol.py by scripts/build_shared.py. Do not edit.\n' + (root / 'shared/protocol.py').read_text()
parser = argparse.ArgumentParser()
parser.add_argument('--check', action='store_true')
args = parser.parse_args()
for target in ['dify/valen_protocol.py', 'langchain/langchain_valen/_protocol.py', 'coze/src/protocol.py']:
    path = root / target
    if args.check:
        if not path.exists() or path.read_text() != source:
            raise SystemExit(f'Stale generated protocol: {target}')
    else:
        path.write_text(source)

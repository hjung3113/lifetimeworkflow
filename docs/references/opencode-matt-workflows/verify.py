#!/usr/bin/env python3
import subprocess,sys
from pathlib import Path
r=Path(__file__).resolve().parent
x=subprocess.run([sys.executable,str(r/'verify-bundle.py')])
if x.returncode:raise SystemExit(x.returncode)
raise SystemExit(subprocess.run([sys.executable,str(r/'doctor.py'),sys.argv[1] if len(sys.argv)>1 else str(r)]).returncode)

"""Check send_realtime_input signature and Modality enum values."""
from google.genai.live import AsyncSession
from google.genai import types
import inspect

sig = inspect.signature(AsyncSession.send_realtime_input)
print("send_realtime_input sig:", sig)

# Check Modality enum
print("Modality values:", [m for m in dir(types.Modality) if not m.startswith("_")])

# Check FunctionDeclaration constructor
sig2 = inspect.signature(types.FunctionDeclaration)
print("FunctionDeclaration sig:", sig2)

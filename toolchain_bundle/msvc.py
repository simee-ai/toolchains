"""Microsoft Visual C++ runtime filenames and redistribution terms."""

import re

MSVC = re.compile(r"(vcruntime140(_\d)?|msvcp140(_\w+)?|concrt140|vccorlib140)\.dll", re.I)
MSVC_TERMS = "https://learn.microsoft.com/en-us/visualstudio/releases/2022/redistribution#visual-c-runtime-files"

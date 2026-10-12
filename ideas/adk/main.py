#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Uruchamiacz główny dla Samoewoluującego Harnessa.
Pozwala na uruchomienie eksperymentu bezpośrednio z folderu ideas/adk.
"""

import sys
from pathlib import Path

# Przekieruj do katalogu harness_mvp
harness_dir = Path(__file__).resolve().parent / "harness_mvp"
sys.path.insert(0, str(harness_dir))

from main import main

if __name__ == "__main__":
    main()


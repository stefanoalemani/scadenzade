#!/usr/bin/env python3
# Entry point esterno per avviare l'applicazione scadenzade

import sys
import os

# Aggiunge src/ al path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), 'src')))

import scadenzade

if __name__ == '__main__':
    scadenzade.main()
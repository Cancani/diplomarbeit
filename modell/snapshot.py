"""Einheitliche Darstellung und Hash eines geprüften Modells."""
import hashlib
import json

from modell.validierung import validate_model


def encode_snapshot(model):
    validate_model(model)
    document = json.dumps(model, ensure_ascii=False, sort_keys=True,
                          separators=(',', ':'), allow_nan=False)
    return document, hashlib.sha256(document.encode('utf-8')).hexdigest()

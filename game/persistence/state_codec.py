import base64
from dataclasses import fields, is_dataclass
import hashlib
import io
import json
import pickle


def _schema_signature(registry):
    description = [
        (
            name,
            [
                state_field.name
                for state_field in fields(state_type)
            ]
            if is_dataclass(state_type)
            else [],
        )
        for name, state_type in sorted(registry.items())
    ]
    encoded = json.dumps(
        description,
        separators=(",", ":"),
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def encode_state(value, registry, persistent_id):
    class StatePickler(pickle.Pickler):
        def persistent_id(self, item):
            return persistent_id(item)

    buffer = io.BytesIO()
    StatePickler(buffer, protocol=4).dump(value)

    return {
        "format": "crypta-state-1",
        "schema": _schema_signature(registry),
        "payload": base64.b64encode(
            buffer.getvalue()
        ).decode("ascii"),
    }


def decode_state(snapshot, registry, persistent_load):
    if (
        not isinstance(snapshot, dict)
        or snapshot.get("format") != "crypta-state-1"
        or snapshot.get("schema") != _schema_signature(registry)
    ):
        raise ValueError(
            "The saved run is incompatible with this game version."
        )

    payload = snapshot.get("payload")
    if not isinstance(payload, str):
        raise ValueError("Invalid saved run payload.")

    class StateUnpickler(pickle.Unpickler):
        def find_class(self, module, name):
            identifier = f"{module}.{name}"
            if identifier not in registry:
                raise pickle.UnpicklingError(
                    f"Unsupported saved type: {identifier}"
                )
            return registry[identifier]

        def persistent_load(self, identifier):
            return persistent_load(identifier)

    raw = base64.b64decode(payload, validate=True)
    buffer = io.BytesIO(raw)
    result = StateUnpickler(buffer).load()

    if buffer.read(1):
        raise ValueError("Unexpected data after the saved run.")

    return result

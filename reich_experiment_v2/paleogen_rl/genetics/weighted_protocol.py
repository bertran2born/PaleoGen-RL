"""Content-addressed weighted pulse inputs; no calibration or CLI adoption."""

from dataclasses import dataclass, fields
import hashlib
import json
from pathlib import Path

from .protocol import AutosomalProtocol, MEASUREMENT, PROTOCOL_VERSION, _canonical, _keys, _unique_fields
from .weighted_ancestry import MEASUREMENT_VERSION, WeightedBlockPanel


WEIGHTED_PROTOCOL_VERSION = 'weighted-autosomal-evaluation-protocol-v1'
WEIGHTED_MEASUREMENT = {
    **MEASUREMENT,
    'measurement_version': MEASUREMENT_VERSION,
    'observable': 'total_weighted_diploid_block_ancestry',
    'weighting': 'explicit_relative_block_weights',
    'target_interval': list(MEASUREMENT['target_interval']),
}


@dataclass(frozen=True)
class WeightedAutosomalProtocol(AutosomalProtocol):
    """I19 pulse/map constraints with a distinct, explicitly weighted measure.

    Mode, selection and seed are execution inputs, not measurement-contract
    inputs. Raw weights and their basis participate in the content identity,
    even when proportional rescaling leaves the observable unchanged.
    """

    measurement_panel: WeightedBlockPanel

    def __post_init__(self):
        super().__post_init__()
        if (not isinstance(self.measurement_panel, WeightedBlockPanel)
                or self.measurement_panel.panel != self.recombination_map.panel):
            raise ValueError('measurement_panel must match the recombination panel identity and order')

    def to_dict(self):
        declaration = super().to_dict()
        declaration.update(
            protocol_version=WEIGHTED_PROTOCOL_VERSION,
            measurement={**WEIGHTED_MEASUREMENT,
                         'target_interval': list(WEIGHTED_MEASUREMENT['target_interval'])},
            measurement_weights=dict(block_weights=list(self.measurement_panel.block_weights),
                                     weight_basis=self.measurement_panel.weight_basis))
        return declaration

    @classmethod
    def from_dict(cls, declaration):
        _keys(declaration, ('protocol_version', 'protocol_id', 'population_size', 'generations',
                            'pulse', 'recombination_map', 'partners', 'measurement',
                            'resolution_control', 'measurement_weights'), 'weighted protocol')
        if declaration['protocol_version'] != WEIGHTED_PROTOCOL_VERSION:
            raise ValueError('unsupported weighted autosomal protocol version')
        if _canonical(declaration['measurement']) != _canonical(WEIGHTED_MEASUREMENT):
            raise ValueError('measurement must use the weighted total and ten-male/3–7% definition')
        weights = declaration['measurement_weights']
        _keys(weights, ('block_weights', 'weight_basis'), 'measurement_weights')
        # Delegate all shared scientific constraints without changing I19's loader
        # or accepting the weighted format through its equal-weight entry point.
        base = AutosomalProtocol.from_dict({
            **{key: value for key, value in declaration.items() if key != 'measurement_weights'},
            'protocol_version': PROTOCOL_VERSION, 'measurement': MEASUREMENT,
        })
        panel = WeightedBlockPanel(base.recombination_map.panel, **weights)
        return cls(**{field.name: getattr(base, field.name) for field in fields(AutosomalProtocol)},
                   measurement_panel=panel)


def _reject_constant(value):
    raise ValueError(f'nonfinite JSON constant: {value}')


def load_weighted_autosomal_protocol(path):
    payload = Path(path).read_bytes()
    declaration = json.loads(payload, object_pairs_hook=_unique_fields, parse_constant=_reject_constant)
    return WeightedAutosomalProtocol.from_dict(declaration), hashlib.sha256(payload).hexdigest()

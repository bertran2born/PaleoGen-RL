"""Explicit, content-addressed autosomal evaluation contracts, not calibration."""

from dataclasses import dataclass
import hashlib
import json
from numbers import Real
from pathlib import Path

from .ancestry import BlockPanel, MEASUREMENT_VERSION
from .inheritance import RecombinationMap


PROTOCOL_VERSION = 'autosomal-evaluation-protocol-v1'
PROTOCOL_RESULT_SCHEMA_VERSION = 'block-pulse-result-v3'
MEASUREMENT = dict(measurement_version=MEASUREMENT_VERSION,
                   observable='total_diploid_block_ancestry', weighting='equal_diploid_copies',
                   sample_size=10, sample_replacement=False, target_interval=[.03, .07])


def _canonical(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'), ensure_ascii=False, allow_nan=False)


def _keys(value, expected, field):
    if not isinstance(value, dict) or set(value) != set(expected):
        raise ValueError(f'{field} must declare exactly {", ".join(expected)}')


def _unique_fields(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f'duplicate protocol field: {key}')
        result[key] = value
    return result


@dataclass(frozen=True)
class AutosomalProtocol:
    protocol_id: str
    population_size: int
    generations: int
    f: float
    male_fraction: float
    recombination_map: RecombinationMap
    mt_partner_block: str
    y_partner_block: str

    def __post_init__(self):
        if (not isinstance(self.protocol_id, str) or not self.protocol_id
                or self.protocol_id != self.protocol_id.strip()):
            raise ValueError('protocol_id must be a nonempty trimmed string')
        if type(self.population_size) is not int or self.population_size < 20:
            raise ValueError('population_size must be an integer >= 20')
        if type(self.generations) is not int or self.generations < 1:
            raise ValueError('generations must be an integer >= 1')
        for field in ('f', 'male_fraction'):
            value = getattr(self, field)
            if isinstance(value, bool) or not isinstance(value, Real) or not 0 <= value <= 1:
                raise ValueError(f'{field} must be finite in [0,1]')
            object.__setattr__(self, field, float(value))
        if not isinstance(self.recombination_map, RecombinationMap):
            raise ValueError('recombination_map must be a RecombinationMap')
        for partner in (self.mt_partner_block, self.y_partner_block):
            if not isinstance(partner, str) or partner not in self.recombination_map.panel.block_ids:
                raise ValueError('partner blocks must belong to the declared panel')
        male_n = self.population_size//2
        if (round(self.f*self.population_size*self.male_fraction) > male_n
                or round(self.f*self.population_size*(1-self.male_fraction)) > self.population_size-male_n):
            raise ValueError('modern pulse exceeds the number of individuals of that sex')

    def to_dict(self):
        mapping = self.recombination_map
        return dict(protocol_version=PROTOCOL_VERSION, protocol_id=self.protocol_id,
                    population_size=self.population_size, generations=self.generations,
                    pulse=dict(f=self.f, male_fraction=self.male_fraction),
                    recombination_map=dict(panel=dict(panel_id=mapping.panel.panel_id,
                                                       block_ids=list(mapping.panel.block_ids)),
                                           switch_probabilities=list(mapping.switch_probabilities)),
                    partners=dict(mt=self.mt_partner_block, y=self.y_partner_block),
                    measurement={**MEASUREMENT, 'target_interval': list(MEASUREMENT['target_interval'])},
                    resolution_control=dict(status='not_established'))

    @property
    def canonical_json(self):
        return _canonical(self.to_dict())

    @property
    def sha256(self):
        return hashlib.sha256(self.canonical_json.encode('utf-8')).hexdigest()

    @classmethod
    def from_dict(cls, declaration):
        _keys(declaration, ('protocol_version', 'protocol_id', 'population_size', 'generations',
                            'pulse', 'recombination_map', 'partners', 'measurement', 'resolution_control'), 'protocol')
        if declaration['protocol_version'] != PROTOCOL_VERSION:
            raise ValueError('unsupported autosomal protocol version')
        _keys(declaration['pulse'], ('f', 'male_fraction'), 'pulse')
        _keys(declaration['partners'], ('mt', 'y'), 'partners')
        _keys(declaration['recombination_map'], ('panel', 'switch_probabilities'), 'recombination_map')
        mapping = declaration['recombination_map']
        _keys(mapping['panel'], ('panel_id', 'block_ids'), 'panel')
        if _canonical(declaration['measurement']) != _canonical(MEASUREMENT):
            raise ValueError('measurement must use the unchanged I11 total and ten-male/3–7% definition')
        if declaration['resolution_control'] != {'status': 'not_established'}:
            raise ValueError('resolution_control must remain not_established; evidence is not validated here')
        return cls(protocol_id=declaration['protocol_id'], population_size=declaration['population_size'],
                   generations=declaration['generations'], f=declaration['pulse']['f'],
                   male_fraction=declaration['pulse']['male_fraction'],
                   recombination_map=RecombinationMap(BlockPanel(**mapping['panel']), mapping['switch_probabilities']),
                   mt_partner_block=declaration['partners']['mt'], y_partner_block=declaration['partners']['y'])


def load_autosomal_protocol(path):
    payload = Path(path).read_bytes()
    declaration = json.loads(payload, object_pairs_hook=_unique_fields)
    return AutosomalProtocol.from_dict(declaration), hashlib.sha256(payload).hexdigest()

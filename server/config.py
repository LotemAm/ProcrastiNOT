import os
import json
from typing import List, Union
from dataclasses import dataclass


@dataclass
class BlockadeConfig:
    name: str
    items: List[str]
    repeat: dict
    start: dict
    duration: Union[int, float]


class Configuration:
    default_path = 'conf.json'

    def __init__(self, path: str = None) -> None:
        self.blockades: List[BlockadeConfig] = []

        if not path:
            path = Configuration.default_path
        if os.path.isfile(path):
            data = json.load(open(path, 'r'))
            for sch in data:
                self.add_scheduled(sch)

    def dump(self, path: str = None) -> None:
        if not path:
            path = Configuration.default_path
        with open(path, 'w') as out_f:
            json.dump(self.blockades, out_f)

    def add_scheduled(self, schedule_data: dict) -> None:
        self.blockades.append(BlockadeConfig(**schedule_data))

    def remove_scheduled(self, name: str) -> None:
        self.blockades = [bl for bl in self.blockades if bl.name != name]

    @property
    def items(self) -> List[str]:
        items = set()
        for bl in self.blockades:
            items.update(bl.items)
        return list(items)


if __name__ == '__main__':
    cfg = Configuration('example_config.json')

import atexit
import datetime
from abc import ABC, abstractmethod
from enum import IntEnum
from json import JSONEncoder
from typing import List, Set, Union

# TODO: Consider using Flask-APScheduler
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.date import DateTrigger

from config import Configuration


class Serializable(ABC):
    @abstractmethod
    def serialize(self):
        raise NotImplementedError


class ProcNOTJsonEncoder(JSONEncoder):
    def default(self, o):
        if isinstance(o, Serializable):
            return o.serialize()

        return super().default(o)


class Item(Serializable):
    def __init__(self, name: str) -> None:
        self.name = name
        self.blockades: Set[Blockade] = set()

    @property
    def blocked(self) -> bool:
        return any(map(lambda bl: bl.active, self.blockades))

    def serialize(self) -> dict:
        return {
            'name': self.name,
            'blocked': self.blocked
        }


class Repetition(Serializable):
    class Type(IntEnum):
        DAILY = 1
        WEEKLY = 2
        CUSTOM = 3

    def __init__(self, repeat_type: str, days: Union[List[str], None]) -> None:
        self.type = self.Type[repeat_type.upper()]
        self.days = days

        assert self.type == self.Type.DAILY or self.days != None, \
            'Weekly or Custom repetition must have days'

    def to_apscheduler_trigger(self, start_time: datetime.time) -> CronTrigger:
        if self.type == self.Type.DAILY:
            return CronTrigger(year='*', month='*', day='*', hour=start_time.hour, minute=start_time.minute)

    def serialize(self) -> dict:
        d = {'type': self.type.name}
        if self.days:
            d['days'] = self.days
        return d


class Blockade(Serializable):
    def __init__(self, name: str, duration: float, repeat: Repetition, start: datetime.time) -> None:
        self.name = name
        self.items: Set[Item] = set()
        self.duration = duration
        self.repeat = repeat
        self.start = start

        self.active = False

    def serialize(self) -> dict:
        return {
            'name': self.name,
            'items': list(self.items),
            'repeat': self.repeat
        }


class ProcrastiNOT:
    def __init__(self, config_path: str = None) -> None:
        self._bg_scheduler = BackgroundScheduler()
        atexit.register(lambda: self._bg_scheduler.shutdown()
                        if self._bg_scheduler.running else None)

        self.items: Set[Item] = []
        self.blockades: List[Blockade] = []

        self.config = Configuration(config_path)
        self._populate_from_config()

    def _populate_from_config(self) -> None:
        for it in self.config.items:
            self.items.append(Item(it))

        for bl in self.config.blockades:
            self.blockades.append(
                Blockade(
                    bl.name,
                    bl.duration,
                    Repetition(bl.repeat['type'], bl.repeat.get('days')),
                    datetime.time.fromisoformat(bl.start)
                )
            )
            blockade = self.blockades[-1]
            for it in bl.items:
                item = next((item for item in self.items if item.name == it))
                blockade.items.add(item)
                item.blockades.add(blockade)

    def _start_blockade(self, blockade: Blockade):
        assert blockade.active == False, 'Trying to start an already active blockade'
        print(f'Starting blockaed {blockade.name}')
        blockade.active = True

        # Create stop job to run in `blockade.duration` minutes from now
        trigger = DateTrigger(datetime.datetime.now() +
                              datetime.timedelta(minutes=blockade.duration))
        self._bg_scheduler.add_job(
            self._stop_blockade, id=f'stop_{blockade.name}', trigger=trigger, args=(blockade,))

    def _stop_blockade(self, blockade: Blockade):
        assert blockade.active == True, 'Trying to stop an already stopped blockade'
        print(f'Stopping blockaed {blockade.name}')
        blockade.active = False

    def init_schedules(self) -> None:
        # TODO: Check and activate a bloackade that should already be running
        for bl in self.blockades:
            trigger = bl.repeat.to_apscheduler_trigger(bl.start)
            self._bg_scheduler.add_job(
                self._start_blockade, id=f'start_{bl.name}', trigger=trigger, args=(bl,))

        self._bg_scheduler.start()

# -*- coding: utf-8 -*-
"""Lorem ipsum

Created on2025.06.04
@author: widmo
"""


from __future__ import annotations
from typing import NamedTuple, Callable
import logging


logging.basicConfig(filename='../logs/latest.log', encoding='utf-8', level=logging.DEBUG)
log = logging.getLogger(__name__)
# log.setLevel(logging.DEBUG)


class Item(NamedTuple):
    name: str
    stack_size: int
    mass: int


class ItemStack(object):
    item: Item
    count: int

    @property
    def mass(self) -> int:
        return self.count * self.item.mass


    def __init__(self, item: Item, count: int=1) -> ItemStack:
        log.debug(f"Creating ItemStack of {count}x {item.name}")

        self.item = item
        if count > item.stack_size:
            raise ValueError(f"{count} exceeds the stack_size of {item.name} ({item.stack_size})")
        self.count = count


    def add(self, count: int) -> int:
        assert count >= 0

        if self.count + count > self.item.stack_size:
            # (Item)Stack Overflow :)
            remainder = self.count + count - self.item.stack_size
            self.count = self.item.stack_size
            # TODO: add logging for item overflow
            return remainder
        else:
            self.count += count
            return 0


class SlotInventory(object):
    slot_count: int
    slots: list[ItemStack | None]

    @property
    def is_empty(self) -> bool:
        result = True
        for slot in self.slots:
            if slot is None:
                continue
            else:
                result = False
                break
        return result


    def __init__(self, slot_count) -> SlotInventory:
        self.slot_count = slot_count

        slots = []
        for i in range(slot_count):
            slots.append(None)
        self.slots = slots


    def give(self, item: Item, count: int=1) -> int:
        """Add an Item to the Inventory."""
        log.debug(f"Adding {count}x {item.name} to SlotInventory")
        assert count >= 0

        # Check for partial stacks
        for slot in self.slots:
            if slot is None:
                # empty stack
                continue

            if slot.item == item:
                count = slot.add(count)
                if count == 0:
                    # No overflow; everything could fit into this stack
                    return 0
                else:
                    # Stack overflowed; distribute the remainder
                    continue
            else:
                # different Item
                continue


        # Check for empty slots
        for i, slot in enumerate(self.slots):
            if slot is None:
                if count > item.stack_size:
                    # can't fit in single stack; distribute the remainder
                    self.slots[i] = ItemStack(item, item.stack_size)
                    count -= item.stack_size
                    continue
                else:
                    # No overflow; everything could fit into this stack
                    self.slots[i] = ItemStack(item, count)
                    return 0

        # Not enough room to distribute all items
        return count


    def list_items(self, template: str="{}: {}x {}") -> None:
        if self.is_empty:
            result = "~Empty~"
        else:
            stacks = []
            for i, slot in enumerate(self.slots):
                if slot is None:
                    continue
                else:
                    stacks.append(template.format(i, slot.count, slot.item.name))
            result = "\n".join(stacks)

        print(result)


if __name__ == "__main__":
    inv = SlotInventory(10)
    inv.list_items()

    item1 = Item("Item 1", 64, 1)

    r = inv.give(item1, 100)

    r = inv.give(item1, 100)
    inv.list_items()

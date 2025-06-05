# -*- coding: utf-8 -*-
"""Lorem ipsum

Created on2025.06.04
@author: widmo
"""


from __future__ import annotations
from typing import NamedTuple, Callable, Counter
import logging


# Needed because the logger doesn't clear the log file, despite being explicitly set to "wt"
with open('../logs/latest.log', "w"):
    pass
logging.basicConfig(filename='../logs/latest.log', filemode="wt", encoding='utf-8', level=logging.DEBUG)
log = logging.getLogger(__name__)
# log.setLevel(logging.DEBUG)


class Item(NamedTuple):
    name: str
    stack_size: int
    mass: float


    # __repr__() inherited from NamedTuple

    def __str__(self) -> str:
        return self.name


class ItemStack(object):
    item: Item
    count: int

    @property
    def mass(self) -> float:
        return self.count * self.item.mass


    def __repr__(self) -> str:
        return f"ItemStack({self.count}, {repr(self.item)})"


    def __str__(self) -> str:
        return f"{self.count}x {str(self.item)}"


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
            log.debug(f"Can't add {count}x {self.item} to a stack of {self.count}; pushing {remainder} to next available slot")
            self.count = self.item.stack_size
            return remainder
        else:
            self.count += count
            return 0


    def remove(self, count: int) -> int:
        assert count >= 0

        if self.count - count >= 0:
            self.count -= count
            return 0

        else:
            remainder = count - self.count
            log.debug(f"Can't take {count}x {self.item} from a stack of {self.count}; pulling {remainder} from next available slot")
            self.count = 0
            return remainder


class SlotInventory(object):
    name: str
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

    @property
    def mass(self) -> float:
        result = 0.0
        for slot in self.slots:
            if slot is None:
                continue
            else:
                result += slot.mass
        return result


    def __repr__(self) -> str:
        return f"SlotInventory(name='{self.name}', slot_count={self.slot_count}, slots={repr(self.slots)})"


    def __str__(self, template: str="  {}: {}") -> str:
        content_list = []
        for i, slot in enumerate(self.slots):
            if slot is None:
                continue
            else:
                content_list.append(template.format(i + 1, slot))

        if len(content_list) > 0:
            contents = "\n".join(content_list)
        else:
            contents = "  ~Empty~"
        return f"{self.name} contents:\n{contents}\n  ({self.slot_count} slots)"



    def __init__(self, name: str="Inventory", slot_count: int=10) -> SlotInventory:
        log.debug(f"Creating new SlotInventory '{name}' with {slot_count} slots")
        self.name = name
        self.slot_count = slot_count

        slots = []
        for i in range(slot_count):
            slots.append(None)
        self.slots = slots


    def give(self, item: Item, count: int=1) -> int:
        """Add Items to the Inventory.

        Return value is how many items were leftover (i.e. how many didn't fit).
        Returns 0 if all items could fit into the inventory.
        """
        log.debug(f"Adding {count}x {item} to '{self.name}'")
        # this should probably be an if that throws a ValueError,
        # but this is simpler and works
        assert count >= 0

        # Check for partial stacks
        for slot in self.slots:
            if slot is None:
                # empty stack
                continue

            elif slot.item == item:
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
        log.debug(f"Failed to fit items into partial stacks, distributing {count}x {item} to empty slots")
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
        log.debug(f"Failed to fit items into '{self.name}'; {count}x {item} left over")
        return count


    def take(self, item: Item, count: int=1) -> int:
        log.debug(f"Removing {count}x {item} from '{self.name}'")
        # this should probably be an if that throws a ValueError,
        # but this is simpler and works
        assert count >= 0

        for index, slot in enumerate(reversed(self.slots)):
            if slot is None:
                # empty stack
                continue

            elif slot.item == item:
                slot_id = self.slot_count - index - 1
                count = slot.remove(count)
                if slot.count == 0:
                    log.debug(f"Stack in slot {slot_id} of '{self.name}' is empty; removing")
                    self.slots[slot_id] = None

                if count == 0:
                    # No underflow; everything could be taken from this slot
                    return 0
                else:
                    # Stack underflowed; take remainder from other slots
                    continue
            else:
                # different Item
                continue

        # Not enough items to tak everything
        log.debug(f"Failed to take items from '{self.name}'; {count}x {item} missing")
        return count


class Inventory(object):
    name: str
    contents: Counter

    @property
    def is_empty(self) -> bool:
        for item, count in self.contents.items():
            # the check is probably unnecessary but eh
            if count > 0:
                return False
            else:
                log.error(f"{self.name} contains {count}x {item}")
        return True

    @property
    def mass(self) -> float:
        result = 0.0
        for item, count in self.contents.items():
            result += item.mass * count
        return result


    def __init__(self, name: str="Inventory") -> Inventory:
        log.debug(f"Creating new Inventory '{name}'")
        self.name = name
        self.contents = Counter()


    def __repr__(self) -> str:
        return f"Inventory(name='{self.name}', contents={self.contents})"


    def __str__(self, template: str="  {}: {}x {}") -> str:
        content_list = []
        for i, (item, count) in enumerate(self.contents.items()):
            content_list.append(template.format(i + 1, count, item))

        if len(content_list) > 0:
            contents = "\n".join(content_list)
        else:
            contents = "  ~Empty~"
        return f"{self.name} contents:\n{contents}"


    def give(self, item: Item, count: int=1) -> int:
        """Add Items to the Inventory.

        Return value is how many items were leftover (i.e. how many didn't fit).
        Returns 0 if all items could fit into the inventory.
        """
        log.debug(f"Adding {count}x {item} to '{self.name}'")
        # this should probably be an if that throws a ValueError,
        # but this is simpler and works
        assert count >= 0

        self.contents[item] += count
        # Compared to SlotInventory, this is comically short
        return 0


    def take(self, item: Item, count: int=1) -> int:
        log.debug(f"Removing {count}x {item} from '{self.name}'")
        # this should probably be an if that throws a ValueError,
        # but this is simpler and works
        assert count >= 0

        if self.contents[item] >= count:
            self.contents[item] -= count
            remainder = 0
        else:
            remainder = count - self.contents[item]
            log.debug(f"Failed to take items from '{self.name}'; {remainder}x {item} missing")
            self.contents[item] = 0

        if self.contents[item] == 0:
            del self.contents[item]

        return remainder


if __name__ == "__main__":
    inv = Inventory("Test Inventory")
    print(inv, "\n")

    apple = Item("Apple", 10, 0.125)

    inv.give(apple, 10)
    print(inv, "\n")

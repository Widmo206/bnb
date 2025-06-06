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
            remainder = 0
            removed = count

        else:
            removed = self.count
            remainder = count - self.count
            log.debug(f"Can't remove {count}x {self.item} from a stack of {self.count}; pulling {remainder} from next available slot")
            self.count = 0

        return removed


class SlotInventory(object):
    name: str
    slot_count: int
    slots: list[ItemStack | None]

    @property
    def is_empty(self) -> bool:
        """Check if the Inventory is empty."""
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
        """Tally up the mass of contained Items."""
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

        return f"{self.name} contents:\n{contents}\n  ({len(content_list)}/{self.slot_count})"



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
        taken = 0

        for index, slot in enumerate(reversed(self.slots)):
            if slot is None:
                # empty stack
                continue

            elif slot.item == item:
                slot_id = self.slot_count - index - 1
                removed = slot.remove(count-taken)
                taken += removed
                if slot.count == 0:
                    log.debug(f"Stack in slot {slot_id} of '{self.name}' is empty; removing")
                    self.slots[slot_id] = None

                if taken == count:
                    # No underflow; everything could be taken from this slot
                    return taken
                else:
                    # Stack underflowed; take remainder from other slots
                    continue
            else:
                # different Item
                continue

        # Not enough items to tak everything
        log.debug(f"Failed to take items from '{self.name}'; {count-taken}x {item} missing")
        return taken


    def contains(self, item: Item, count: int=1) -> bool:
        """Check if the given Inventory has the specified amount of an item.

        Useful when you want an action to be performed *only* if a sufficient
        quantity of an Item is present.
        """
        amount = 0
        for slot in self.slots:
            if slot is None:
                # empty stack
                continue

            elif slot.item == item:
                amount += slot.count
                if amount >= count:
                    return True
            else:
                continue
        return False


    def has_space_for(self, item: Item, count: int) -> bool:
        """Check if the given SlotInventory can accept x amount of an Item."""
        available_space = 0

        for slot in self.slots:
            if slot is None:
                available_space += item.stack_size

            elif slot.item == item:
                available_space += item.stack_size - slot.count

            else:
                pass
            if available_space >= count:
                return True

        return False


    def transfer(self, target: Inventory, item: Item, count: int=1) -> None:
        log.debug(f"Transfering {count}x {item} from '{self.name}' to '{target.name}'")

        actual_count = self.take(item, count)
        if actual_count < count:
            log.debug(f"Transfer issue: '{self.name}' only contained {actual_count}x {item} ")

        if actual_count > 0:
            overflow = target.give(item, actual_count)
            if overflow > 0:
                log.debug(f"Transfer issue: '{target.name}' could only accept {actual_count-overflow}x {item}; {overflow} returned to '{self.name}'")
                self.give(item, overflow)


class Inventory(object):
    name: str
    contents: Counter

    @property
    def is_empty(self) -> bool:
        """Check if the Inventory is empty."""
        for item, count in self.contents.items():
            # the check is probably unnecessary but eh
            if count > 0:
                return False
            else:
                log.error(f"{self.name} contains {count}x {item}")
        return True

    @property
    def mass(self) -> float:
        """Tally up the mass of contained Items."""
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
            # TODO add padding
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
        """Remove items from the inventory and return how many were removed."""
        log.debug(f"Removing {count}x {item} from '{self.name}'")
        # this should probably be an if that throws a ValueError,
        # but this is simpler and works
        assert count >= 0

        if self.contents[item] >= count:
            self.contents[item] -= count
            remainder = 0
            taken = count
        else:
            taken = self.contents[item]
            remainder = count - self.contents[item]
            log.debug(f"Failed to take items from '{self.name}'; {remainder}x {item} missing")
            self.contents[item] = 0

        if self.contents[item] == 0:
            del self.contents[item]

        return taken
        # return remainder


    def transfer(self, target: Inventory, item: Item, count: int=1) -> None:
        log.debug(f"Transfering {count}x {item} from '{self.name}' to '{target.name}'")

        actual_count = self.take(item, count)
        if actual_count < count:
            log.debug(f"Transfer issue: '{self.name}' only contained {actual_count}x {item} ")

        if actual_count > 0:
            overflow = target.give(item, actual_count)
            if overflow > 0:
                log.debug(f"Transfer issue: '{target.name}' could only accept {actual_count-overflow}x {item}; {overflow} returned to '{self.name}'")
                self.give(item, overflow)



    def contains(self, item: Item, count: int=1) -> bool:
        """Check if the given Inventory has the specified amount of an item.

        Useful when you want an action to be performed *only* if a sufficient
        quantity of an Item is present.
        """
        return self.contents[item] >= count


    def has_space_for(self, item: Item, count: int) -> bool:
        """Check if the given Inventory can accept x amount of an Item.

        Not really needed for a slotless Inventory, but will make some logic
        simpler when mixing inventory types.
        """
        # kinda pointless for a slotless Inventory, but will be needed for
        # SlotInventory, so might as well have it here so I don't need separate
        # logic for slotted and slotless inventories
        return True


if __name__ == "__main__":
    inv = Inventory("Test Inventory")

    apple = Item("Apple", 10, 0.125)

    inv.give(apple, 20)
    print(inv, "\n")

    bag = Inventory("Bag")
    print(bag, "\n")

    box = SlotInventory("Box", 10)
    box.give(apple, 30)
    print(box)

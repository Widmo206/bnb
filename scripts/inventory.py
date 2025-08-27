# -*- coding: utf-8 -*-
"""Lorem ipsum

Created on2025.06.04
@author: widmo
"""


from __future__ import annotations
from typing import NamedTuple, Callable, Counter, Collection
# from types import MappingProxyType
from uuid import UUID, uuid4
import logging
from get_input import get_input


# Needed because the logger doesn't clear the log file, despite being explicitly set to "wt"
with open('../logs/latest.log', "w"):
    pass
logging.basicConfig(filename='../logs/latest.log', filemode="wt", encoding='utf-8', level=logging.DEBUG)
log = logging.getLogger(__name__)
# log.setLevel(logging.DEBUG)


def main():
    ...


def print_list(lst: Collection, offset: int=0, _filter: Callable=None, processor: Callable=None,
               header: str=None, template: str="  {}: {}", empty: str="  ~Empty~") -> None:
    if _filter is None:
        _filter = lambda x: True

    if processor is None:
        processor = lambda x: str(x)

    if header is None:
        result = ""
    else:
        result = "\n" + header

    if len(lst) > 0:
        for i, item in enumerate(lst):
            if not _filter(item):
                continue

            result += "\n" + template.format(i + offset, processor(item))
    else:
        result += "\n" + empty

    print(result)







class InventoryNotFoundError(KeyError):
    """Raised when referencing a non-existant or deleted inventory."""
    pass


class InventoryInterface(object):
    """Contains methods allowing the player to interact with an inventory."""
    inventory: Inventory | SlotInventory
    inventory_id: UUID
    inventory_handler: InventoryHandler
    # I could have had a tuple for commands and a tuple for the names, but
    # this seems less error-prone (I can't mess up the indeces because they're
    # one element)
    actions: tuple[(str, Callable)]


    def __init__(self, inventory_handler: InventoryHandler, inventory_id: UUID):
        self.inventory_handler = inventory_handler
        self.inventory_id = inventory_id
        self.inventory = inventory_handler.get(inventory_id)
        self.actions = (
        # ("Command Name", self.command),
        # TODO
        ("Back", NotImplemented),
        ("List Contents", self.list_items),
        ("Transfer Items", self.transfer),

        )


    def list_items(self) -> None:
        """Print the inventory's contents to the console."""
        print(self.inventory.__str__())


    def list_actions(self, template: str="  {}: {}") -> None:
        """Lists the available actions regarding the given inventory."""
        # probably not needed
        assert len(self.actions) > 0

        result = "Available actions:"

        for i, (action_name, action) in enumerate(self.actions):
            result += "\n" + template.format(i, action_name)

        print(result)


    def get_user_action(self) -> Callable:
        choice_index = get_input(int, True, (0, len(self.actions) - 1))

        return self.actions[choice_index][1]


    def open(self) -> None:
        self.list_actions()
        self.get_user_action()()


    def get_inventories(self) -> list[UUID]:
        inventories = self.inventory_handler.list_ids()
        inventories.remove(self.inventory_id)

        return inventories


    def printlist(data: list | tuple, header: str="Data:", start_offset: int=1,
                  _filter: Callable=lambda d: True,
                  processor: Callable=None, template: str="  {}: {}") -> None:

        result = ""
        for i, entry in enumerate(data):
            if not _filter(entry):
                continue
            if processor is not None:
                processed_entry = processor(entry)
            else:
                processed_entry = entry

            result += "\n" + template.format(i + start_offset, processed_entry)



    def list_inventories(self, template: str="  {}: {}") -> None:
        inventories = self.inventory_handler.list_ids()
        inventories.remove(self.inventory_id)

        result = "Accessible inventories:"

        for i, uuid in enumerate(inventories):
            result += "\n" + template.format(i + 1, self.inventory_handler.get(uuid).name)

        print(result)


    def transfer(self) -> None:
        self.list_items()

        # TODO: implement occupied_slots() for both inv types

        self.list_inventories()

        #TODO: implement choosing inventory










class InventoryHandler(NamedTuple):
    """Stores inventories on behalf of immutable objects (like Items)."""
    inventories: dict[UUID, Inventory | SlotInventory]


    @staticmethod
    def _init() -> InventoryHandler:
        inventories = {}

        return InventoryHandler(inventories)


    def add(self, inventory: Inventory | SlotInventory) -> UUID:
        """Add an inventory to the handler."""
        reference_id = uuid4()

        self.inventories[reference_id] = inventory

        return reference_id


    def get(self, reference_id) -> Inventory | SlotInventory:
        """Return the inventory stored under the given reference."""
        if reference_id in self.inventories.keys():
            return self.inventories[reference_id]
        else:
            raise InventoryNotFoundError(f"Could not find inventory with UUID {reference_id}")


    def remove(self, reference_id) -> None:
        """Add an inventory from the handler."""
        log.debug(f"Deleting reference to '{self.get(reference_id).name}' for {reference_id}")
        del self.inventories[reference_id]


    def list_ids(self) -> list[UUID]:
        """Return a list of UUIDs for all inventories registered in this InventoryHandler."""
        return list(self.inventories.keys())


    def open(self, reference_id) -> None:
        """Open the specified inventory in an InventoryInterface."""
        interface = InventoryInterface(self, reference_id)

        interface.open()


    def _choose_inv(self) -> None:
        inventory_ids = self.list_ids()
        print_list(inventory_ids, offset=1, processor=lambda i: self.get(i).name,
                   header="Available inventories:")
        if len(inventory_ids) <= 0:
            return
        choice = get_input(int, True, (1, len(inventory_ids)))

        inventory_id = inventory_ids[choice - 1]
        interface = InventoryInterface(self, inventory_id)

        interface.open()



class Item(NamedTuple):
    name: str
    stack_size: int
    base_mass: float

    @property
    def mass(self) -> float:
        """Returns the mass of the item.

        For simple items, it's just the base mass. For containers, it's base mass + mass of the contents.
        """
        return self.base_mass


    # __repr__() inherited from NamedTuple

    def __str__(self) -> str:
        return self.name


class ContainerItem(Item):
    """An item with an inventory."""
    inventory_id: UUID

    @property
    def inventory(self) -> Inventory | SlotInventory:
        """Fetch the Item's associated inventory."""
        global inventory_handler

        return inventory_handler.get(self.inventory_id)


class ItemStack(object):
    item: Item
    count: int

    @property
    def mass(self) -> float:
        """Calculate the mass of the ItemStack

        mass = count * item.mass
        """
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

    IH = InventoryHandler._init()
    inv_id = IH.add(inv)
    inv_if = InventoryInterface(IH, inv_id)

    apple = Item("Apple", 10, 0.125)

    inv.give(apple, 20)
    print(inv, "\n")

    bag = Inventory("Bag")
    bag_id = IH.add(bag)
    print(bag, "\n")

    box = SlotInventory("Box", 10)
    box.give(apple, 30)
    box_id = IH.add(box)
    print(box)

    IH._choose_inv()

    main()

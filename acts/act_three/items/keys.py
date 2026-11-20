CRYPTA_KEY = "crypta_key"
KEYRING_ITEMS = ("keyring_empty", "keyring_one", "keyring_two", "keyring_three")
KEYRING_CAPACITY = 3


def store_key_on_ring(slots):
    for index, item in enumerate(slots):
        if item in KEYRING_ITEMS[:-1]:
            slots[index] = KEYRING_ITEMS[KEYRING_ITEMS.index(item) + 1]
            return True
    return False


def collect_loose_keys(slots, ring_index):
    count = KEYRING_ITEMS.index(slots[ring_index])
    for index, item in enumerate(slots):
        if count >= KEYRING_CAPACITY:
            break
        if item == CRYPTA_KEY:
            slots[index] = None
            count += 1
    slots[ring_index] = KEYRING_ITEMS[count]


def combine_key_and_ring(slots, source, target):
    if not (0 <= source < len(slots) and 0 <= target < len(slots)):
        return False
    if slots[source] == CRYPTA_KEY and slots[target] in KEYRING_ITEMS[:-1]:
        slots[target] = KEYRING_ITEMS[KEYRING_ITEMS.index(slots[target]) + 1]
        slots[source] = None
        return True
    if slots[target] == CRYPTA_KEY and slots[source] in KEYRING_ITEMS[:-1]:
        slots[target] = KEYRING_ITEMS[KEYRING_ITEMS.index(slots[source]) + 1]
        slots[source] = None
        return True
    return False

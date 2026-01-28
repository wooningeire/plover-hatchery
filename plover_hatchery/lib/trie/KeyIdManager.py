from collections.abc import Iterable


class KeyIdManager[K]:
    def __init__(self):
        self.__keys_to_ids: dict[K, int] = {}
        self.__keys_list: list[K] = []

    def get_key_id_else_create(self, key: K | None):
        if key is None:
            return None

        if key in self.__keys_to_ids:
            return self.__keys_to_ids[key]
        
        new_key_id = len(self.__keys_to_ids)
        self.__keys_to_ids[key] = new_key_id
        self.__keys_list.append(key)
        return new_key_id

        
    def get_key(self, key_id: int):
        return self.__keys_list[key_id]

        
    def get_key_str(self, key_id: int | None):
        if key_id is None:
            return "(ε)"

        return str(self.__keys_list[key_id])

    def get_key_ids_else_create(self, keys: Iterable[K]):
        return tuple(self.get_key_id_else_create(key) for key in keys)
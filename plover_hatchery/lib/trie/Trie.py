from typing import Generic, TypeVar, final


Key = TypeVar("Key")
Value = TypeVar("Value")

@final
class Trie(Generic[Key, Value]):
    ROOT = 0
    
    def __init__(self):
        self.__nodes: list[dict[int, int]] = [{}]
        self.__translations: dict[int, Value] = {}
        self.__keys: dict[Key, int] = {}

    def get_dst_node_else_create(self, src_node: int, key: Key):
        key_id = self.__get_key_id(key)

        transitions = self.__nodes[src_node]
        if key_id in transitions:
            return transitions[key_id]
        
        new_node_id = len(self.__nodes)
        transitions[key_id] = new_node_id
        self.__nodes.append({})

        return new_node_id

    def get_dst_node_else_create_chain(self, src_node: int, keys: tuple[Key, ...]):
        current_node = src_node
        for key in keys:
            current_node = self.get_dst_node_else_create(current_node, key)
        return current_node
    
    def get_dst_node(self, src_node: int, key: Key):
        key_id = self.__keys.get(key)
        if key_id is None:
            return None
        
        return self.__nodes[src_node].get(key_id)
    
    def get_dst_node_chain(self, src_node: int, keys: tuple[Key, ...]):
        current_node = src_node
        for stroke in keys:
            current_node = self.get_dst_node(current_node, stroke)
            if current_node is None:
                return None
        return current_node
    
    def set_translation(self, node: int, translation: Value):
        self.__translations[node] = translation
    
    def get_translation(self, node: int):
        return self.__translations.get(node)
    
    def frozen(self):
        return ReadonlyTrie(self.__nodes, self.__translations, self.__keys)
    
    def __get_key_id(self, key: Key):
        if key in self.__keys:
            return self.__keys[key]
        
        new_key_id = len(self.__keys)
        self.__keys[key] = new_key_id
        return new_key_id

    def __str__(self):
        lines: list[str] = []

        key_ids_to_keys = self.__key_ids_to_keys()

        for i, transitions in enumerate(self.__nodes):
            translation = self.__translations.get(i, None)
            lines.append(f"""{i}{f" : {translation}" if translation is not None else ""}""")
            for key_id, dst_node in transitions.items():
                lines.append(f"""\t{key_ids_to_keys[key_id]}\t ->\t {dst_node}""")

        return "\n".join(lines)
    
    def __key_ids_to_keys(self):
        return {
            key_id: key
            for key, key_id in self.__keys.items()
        }
    

@final
class ReadonlyTrie(Generic[Key, Value]):
    ROOT = 0

    def __init__(self, nodes: list[dict[int, int]], translations: dict[int, Value], keys: dict[Key, int], support_reverse=False):
        self.__nodes: dict[tuple[int, int], int] = {
            (src_node, key): dst_node
            for src_node, transitions in enumerate(nodes)
            for key, dst_node in transitions.items()
        }
        self.__translations: dict[int, Value] = translations
        self.__keys: dict[Key, int] = keys
    
    def get_dst_node(self, src_node: int, key: Key):
        key_id = self.__keys.get(key)
        if key_id is None:
            return None
        
        return self.__nodes.get((src_node, key_id))
    
    def get_dst_node_chain(self, src_node: int, keys: tuple[Key, ...]):
        current_node = src_node
        for stroke in keys:
            current_node = self.get_dst_node(current_node, stroke)
            if current_node is None:
                return None
        return current_node
    
    def get_translation(self, node: int):
        return self.__translations.get(node)

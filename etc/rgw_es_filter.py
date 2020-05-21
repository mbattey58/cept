import json
from typing import Dict, List, Union


def find_paths(key: str, d: Dict,
               path: List[Union[str, int]] = []) -> List[Union[str, list]]:
    """Returns all paths to a specific key in a dictionary representing
       a json tree.

    Args:
        key (str): key to search for
        d (dict):  dictionary representing a json tree
    Returns:
        list: path to element or None if no path found; path may contain both
              string representing keys and numbers reresenting the position
              of an element in a list.
    """
    if type(d) != dict and type(d) != list:
        return None

    paths = []
    if type(d) == list:
        for i, x in enumerate(d):
            if type(x) == dict:
                p = find_paths(key, x, path + [i])
                if p:
                    paths.extend(p)
    else:
        if key in d.keys():
            paths.append(path + [key])
        for k in d.keys():
            if k == key:
                continue
            p = find_paths(key, d[k], path + [k])
            if p:
                paths.extend(p)
    return paths or None


def sublist_match(l: List, m: List) -> List[int]:
    assert len(m) <= len(l)
    match_indices = []
    for start in range(len(l) - len(m)):
        if l[start: start + len(m)] == m:
            match_indices.append(start)
    return match_indices or None


def dict_node(path: List[Union[str, int]],
              d: Union[Dict, List]) -> Dict:
    """Retrieves node given path.

    Because in json dictionary keys are string and values can be strings,
    dictionaries or list containing values of any kind, list path elements
    are identified with the positional location of the key in the list.

    Returning a leaf value is not supported, however in case the last
    element in path is a number identifying a list element, such element
    can be a string.

    Args:
        path (list): list of strings and/or integers, representing a path
                     to an element; in the case of integers the value
                     represents the position of the element in the list
        d (Union[Dict, List, str]): json dictionary node, string, dict or list
    Returns:
        dict, list or str: dictionary node, or value in case last path element
                           identifies a list element and such element is a
                           string
    """

    if type(d) == list:
        idx = int(path[0])
        if len(d) <= idx:
            return None
        if len(path) == 1:
            return d[idx]
        else:
            return dict_node(path[1:], d[idx])
    elif type(d) == dict:
        if path[0] not in d.keys():
            return None
        if len(path) == 1:
            return d[path[0]]
        else:
            return dict_node(path[1:], d[path[0]])


def test():
    j = dict()
    with open('./etc/rgw-es-wrong.json') as f:
        j = json.load(f)
    paths = find_paths('permissions', j)
    print(paths)
    n = dict_node(paths[0][:-2], j)  # term[-2]/permissions[-1]/content[0]
    print(n)
    n['search'] = n['term']
    del n['term']
    print(n)
    print(j)
    print(json.dumps(n))


def filter_content(content: bytes, headers: dict):
    """Replace 'term' with 'search' above 'permissions' in Ceph elastic
       search request.

    Content is changed only if content-type exists and it is set to
    'application/json'

       Args:
            content (bytes): http request content
            headers (dict):  http request headers
       Returns:
            bytes: changed content
    """
    content_type = None
    for k in headers.keys():
        if k.lower() == "content-type":
            content_type = headers[k]

    if not content_type or content_type != "application/json":
        return content
    j = json.loads(content)
    paths = find_paths('permissions', j)
    if not paths:
        return content
    n = dict_node(paths[0][:-2], j)

    if 'term' not in n.keys():
        return content
    n['search'] = n['term']
    del n['term']
    return json.dumps(j).encode('utf-8')


if __name__ == "__main__":
    test()


# Sample input:
# {"query": {"bool": {"must": [{"term": {"bucket": "obo"}}, 
# {"bool": {"must": [{"term": 
# {"permissions": "2bf7e287aba345c1a3d0a8e177aeccd6$2bf7e287aba345c1a3d0a8e177aeccd6"}}, 
# {"term": {"name": "file100"}}]}}]}}}

# Sample output:
# {"query": {"bool": {"must": [{"term": {"bucket": "obo"}}, 
# {"bool": {"must": [{"search": 
# {"permissions": "2bf7e287aba345c1a3d0a8e177aeccd6$2bf7e287aba345c1a3d0a8e177aeccd6"}}, 
# {"term": {"name": "file100"}}]}}]}}}
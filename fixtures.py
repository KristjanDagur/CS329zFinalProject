"""Synthetic midpoint repair fixtures, not a research benchmark.

Only starter/spec/smoke go into the agent workspace. Independent tests and
reference solutions stay with the evaluator. Sanity tasks are not model-run
during the initial development pilot.
"""
TASKS = {
    "stable_unique": {
        "split": "development",
        "spec": "Fix stable_unique(values): return each distinct hashable value once, in first-occurrence order. Accept arbitrary iterables, including generators. Preserve the original values; do not sort or mutate input. Python equality defines duplicates.",
        "starter": "def stable_unique(values):\n    return sorted(set(values))\n",
        "smoke": "assert stable_unique([3, 1, 3, 2]) == [3, 1, 2]\nassert stable_unique([]) == []\n",
        "tests": """
def test_order(self): self.assertEqual(stable_unique([3,1,3,2,1]), [3,1,2])
def test_generator(self): self.assertEqual(stable_unique(x for x in [4,2,4]), [4,2])
def test_mixed(self): self.assertEqual(stable_unique([None,'a',None,3,'a']), [None,'a',3])
def test_empty(self): self.assertEqual(stable_unique([]), [])
def test_no_mutation(self):
    x=[2,1,2]; stable_unique(x); self.assertEqual(x,[2,1,2])
def test_equality(self): self.assertEqual(stable_unique([True,1,False,0]), [True,False])
""",
        "reference": "def stable_unique(values):\n    return list(dict.fromkeys(values))\n",
    },
    "chunked": {
        "split": "development",
        "spec": "Fix chunked(values, size): return a list of consecutive lists of at most size elements, retaining the final partial chunk. size must be a positive integer; reject zero/negative with ValueError and non-integers (including bool) with TypeError. Consume arbitrary iterables once and never mutate input.",
        "starter": "def chunked(values, size):\n    return [values[i:i+size] for i in range(0, len(values)-size+1, size)]\n",
        "smoke": "assert chunked([1,2,3], 2) == [[1,2],[3]]\nassert chunked([], 2) == []\n",
        "tests": """
def test_tail(self): self.assertEqual(chunked([1,2,3,4,5],2), [[1,2],[3,4],[5]])
def test_generator(self): self.assertEqual(chunked(iter([1,2,3]),2), [[1,2],[3]])
def test_empty(self): self.assertEqual(chunked([],3), [])
def test_large(self): self.assertEqual(chunked([1],8), [[1]])
def test_nonpositive(self):
    for n in [0,-1]:
        with self.assertRaises(ValueError): chunked([],n)
def test_types(self):
    for n in [True,1.5,'2',None]:
        with self.assertRaises(TypeError): chunked([],n)
def test_no_mutation(self):
    x=[1,2,3]; chunked(x,2); self.assertEqual(x,[1,2,3])
""",
        "reference": """def chunked(values, size):
    if not isinstance(size, int) or isinstance(size, bool): raise TypeError('size')
    if size <= 0: raise ValueError('size')
    result, part = [], []
    for value in values:
        part.append(value)
        if len(part) == size:
            result.append(part); part = []
    if part: result.append(part)
    return result
""",
    },
    "merge_intervals": {
        "split": "development",
        "spec": "Fix merge_intervals(intervals): consume an iterable of numeric (start, end) pairs and return sorted, nonoverlapping tuples. Merge overlapping or touching intervals, including nested intervals. Reject a reversed interval (start > end) with ValueError. Do not mutate the input or its nested lists. Empty input returns an empty list.",
        "starter": """def merge_intervals(intervals):
    intervals.sort()
    result = []
    for start, end in intervals:
        if result and start < result[-1][1]:
            result[-1] = (result[-1][0], end)
        else:
            result.append((start, end))
    return result
""",
        "smoke": "assert merge_intervals([(1,5),(2,3)]) == [(1,5)]\nassert merge_intervals([(1,2),(2,4)]) == [(1,4)]\n",
        "tests": """
def test_nested(self): self.assertEqual(merge_intervals([(1,10),(2,3),(4,8)]), [(1,10)])
def test_touching(self): self.assertEqual(merge_intervals([(2,4),(1,2)]), [(1,4)])
def test_separate(self): self.assertEqual(merge_intervals([(5,6),(1,2)]), [(1,2),(5,6)])
def test_generator(self): self.assertEqual(merge_intervals(iter([(1,3),(2,4)])), [(1,4)])
def test_no_mutation(self):
    x=[[5,6],[1,4]]; merge_intervals(x); self.assertEqual(x,[[5,6],[1,4]])
def test_invalid(self):
    with self.assertRaises(ValueError): merge_intervals([(4,2)])
def test_empty(self): self.assertEqual(merge_intervals([]), [])
def test_negative(self): self.assertEqual(merge_intervals([(-3,0),(-1,2),(8,8)]), [(-3,2),(8,8)])
""",
        "reference": """def merge_intervals(intervals):
    pairs = sorted(tuple(p) for p in intervals)
    result = []
    for start,end in pairs:
        if start > end: raise ValueError('interval')
        if result and start <= result[-1][1]:
            result[-1] = (result[-1][0], max(end,result[-1][1]))
        else: result.append((start,end))
    return result
""",
    },
    "normalize_space": {
        "split": "sanity",
        "spec": "Fix normalize_space(text): strip leading/trailing whitespace and collapse all runs of Unicode whitespace to one ASCII space. Preserve all non-whitespace characters and case. Empty/all-whitespace strings return an empty string.",
        "starter": "def normalize_space(text):\n    return text.strip().replace('  ', ' ')\n",
        "smoke": "assert normalize_space(' a   b ') == 'a b'\n",
        "tests": """
def test_runs(self): self.assertEqual(normalize_space('  a    b   '),'a b')
def test_unicode(self): self.assertEqual(normalize_space('a\\u2003b\\u00a0c'),'a b c')
def test_newline(self): self.assertEqual(normalize_space('a\\n\\t b'),'a b')
def test_empty(self): self.assertEqual(normalize_space(' \\n '),'')
""",
        "reference": "def normalize_space(text):\n    return ' '.join(text.split())\n",
    },
    "rolling_mean": {
        "split": "sanity",
        "spec": "Fix rolling_mean(values, window): return means of each complete sliding window, using one pass over an arbitrary iterable. Reject nonpositive integer windows with ValueError and non-integer/bool windows with TypeError. No complete windows means an empty result. Never mutate input.",
        "starter": "def rolling_mean(values, window):\n    return [sum(values[i:i+window])/window for i in range(len(values)-window)]\n",
        "smoke": "assert rolling_mean([1,2,3],2) == [1.5,2.5]\n",
        "tests": """
def test_last(self): self.assertEqual(rolling_mean([1,2,3],2),[1.5,2.5])
def test_iterator(self): self.assertEqual(rolling_mean(iter([2,4]),1),[2,4])
def test_empty(self): self.assertEqual(rolling_mean([],2),[])
def test_invalid(self):
    with self.assertRaises(ValueError): rolling_mean([],0)
def test_type(self):
    with self.assertRaises(TypeError): rolling_mean([],True)
""",
        "reference": """def rolling_mean(values, window):
    from collections import deque
    if not isinstance(window,int) or isinstance(window,bool): raise TypeError('window')
    if window <= 0: raise ValueError('window')
    q=deque(); total=0; result=[]
    for v in values:
        q.append(v); total+=v
        if len(q)>window: total-=q.popleft()
        if len(q)==window: result.append(total/window)
    return result
""",
    },
    "flatten_lists": {
        "split": "sanity",
        "spec": "Fix flatten_lists(value): flatten nested lists into a list of their non-list leaves, in order; other objects (including strings and tuples) are atomic. Accept a non-list root as a single leaf. Do not mutate input. Support at least 2000 levels of nesting without recursion failure.",
        "starter": "def flatten_lists(value):\n    return [leaf for part in value for leaf in part]\n",
        "smoke": "assert flatten_lists([1,[2,[3]]]) == [1,2,3]\n",
        "tests": """
def test_nested(self): self.assertEqual(flatten_lists([1,[2,[],[3]]]),[1,2,3])
def test_atomic(self): self.assertEqual(flatten_lists(['ab',(1,2)]),['ab',(1,2)])
def test_root(self): self.assertEqual(flatten_lists(4),[4])
def test_deep(self):
    v=1
    for _ in range(2000): v=[v]
    self.assertEqual(flatten_lists(v),[1])
""",
        "reference": """def flatten_lists(value):
    result=[]; stack=[value]
    while stack:
        item=stack.pop()
        if isinstance(item,list): stack.extend(reversed(item))
        else: result.append(item)
    return result
""",
    },
}

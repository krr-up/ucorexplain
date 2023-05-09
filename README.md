# ucorexplain


## Installation

Requires Python 3.10

**Local dev mode using pip**

```shell
pip install -e .[dev]
```

## Usage

```shell
ucorexplain -h
```

## Tests

Run tests using `pytest`

```shell
$ pytest -v tests
```

Add flag `-s` to show print statements in the code

## Notes

### Restricted fragment

- No aggregates
- No choices since they are translated into `#count`
- We do not explain well founded
- We avoid the use of branching during solving
    - This is achieved by the way the core is selected, before requiring branching to infer a value, the solver would rather choose such value from the answer set provided

**General disjunction over tight programs**

### Types of inferences

Based on the Clark Completion

- **Support**

    Any rule $r$ such that $a\in H(r)$ then
    - $B(r)$ is true
    - and there  for all $h\in H(r)-{a}$ such that $h$ is false

    *Example*

    - `a | h1 | h2 :- b.`

        **`~h1 ~h2 b` $\to$ `a`**


- **Lack of support**

    Each rule $r$ such that $a\in H(r)$ then
    - either $B(r)$ is False
    - or there is $h\in H(r)-{a}$ such that $h$ is True

    *Example*
    - `a | h1 :- b1.`
      `a | h2 :- b2.`

        **`h1 ~b2` $\to$ `not a`**


- **Constraint like**

    Any rule $r$ such that $a\in B(r)$ then
    if the rest of the body is True, then $a$ cant be True

    *Example*

    - `:- a, b1, not b2.`
      **`b1 ~b2` $\to$ `~a`**
    - `:- not a, b1.`
      **`b1` $\to$ `a`**

- **Last supporting rule**

    If `a` is true and for all rules $r$ such that $a\in H(r)$
    if $\exists_{i}$ such that $ \forall_{j \neq i}\;B(r_j)$ is false.
    - Then $B(r_i)$ must be true

    *Example*

    - `a:-b1.`
      `a:-b2.`

        **`a ~b1` $\to$ `b2`**

- **Well founded**

    Not considered
    Maybe we could say that anything that is not explained using the inferences above, came from well founded.



## TODOS


### Complex development

- [ ] Ask Roland how easy these are to implement

#### Clasp
- [ ] How to know were certain literals come from (Body, auxiliary)
- [ ] Link body variables to ground rules
#### Gringo
- [ ] Link grounded rules to non-ground rules (This was a wish in other projects)


### Multiple queries
- [ ] Revisit Semantic for multiple  queries
- [ ] All queries in the same rule `stop:- q1,q2,....`
- [ ] Propagator to look for `stop` and stop the propagation by propagating `~stop`
- [ ] Keep the `not true` in the assumptions
- [ ] Use the propagator also in the unit propagation to get the proof tree


### Example application
- [ ] Write sudoku with disjunction in the head and without choices
- [ ] Add the proof tree expected output in tests (Copy from mail)
- [ ] Add more tests based on the different inferences
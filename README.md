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

Visualize sudoku

```
clingo examples/sudoku/encoding.lp examples/sudoku/instance.lp --outf=2 | clingraph --viz-encoding examples/sudoku/viz.lp --out=render --view --default-graph=sudoku  --engine=neato
```

Run the pipeline to explain the given query `-q` with answer set `--answer` for the program `--prg`

```shell
ucorexplain --prg examples/basic/choice/prg.lp --answer "a b" -q "b" -i 3
```

## Tests

Run tests using `pytest`

```shell
$ pytest -v tests
```

Add flag `-s` to show print statements in the code

------------------------------------------------------------

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


    *Example*

    - `a :- b1, b2.`

        **Inference: `b1, b2` $\to$ `a`**

        - All nogoods:
            - $\{ T_{B1}, F_{b1} \}$ $\{ T_{B1}, F_{b2} \}$ $\{ F_{B1}, T_{b1}, T_{b2}\}$
            - $\{ T_{B1}, F{a}\}$

        - Reason for $a=\top$ : $\{ T_{B1}, F{a}\}$

        Since it has a true body $T_{B1}$ then is a support inference and we need the support for $B1$

        reason for $B1=\top$: $\{ F_{B1}, T_{b1}, T_{b2}\}$

        We put them together and get $\{ F{a}, T_{b1}, T_{b2}\}$

         *"Is true $a$ because $b1$ is true and $b2$ is true. With rule `a :- b1, b2..` doing a support like inference"*

        $G= b1\to a, b2\to a$

    *Nogood*

    - $\{F_a, T_{b1}\}$
        1. $T_{b1} = true$ $\to$ $T_{a}$
        2. $F_{a} = true$ $\to$ $F_{b1}$


![Alt text](./img/support.svg)

- **Lack of support**

    Each rule $r$ such that $a\in H(r)$ then
    - either $B(r)$ is False
    - or there is $h\in H(r)-{a}$ such that $h$ is True

    *Example*
    - `a | h1 :- b1.`
      `a | h2 :- b2.`

        **`h1 ~b2` $\to$ `not a`**

![Alt text](./img/lack_of_support.svg)


- **Constraint like**

    Any rule $r$ such that $a\in B(r)$ then
    if the rest of the body is True, then $a$ cant be True

    *Example*

    - `:- a, b1, not b2.`
      **`b1 ~b2` $\to$ `~a`**
        - $\{T_a,T_{b1},F_{b2}\}$
        - $b_1=\top$, $b_2=\bot$ $\to a=\bot$

    *Example*
    - `:- not a, b1.`
      **`b1` $\to$ `a`**

    *Example*
    - `h :- not a, b1.`
      `h :- c.`
      **Inference: `b1 ~h` $\to$ `a`**
      - All nogoods:
        - $\{T_{B1},T_{a}\}$ $\{T_{B1},F_{b1}\}$ $\{F_{B1},T_{b1},F_{a}\}$*
        - $\{T_{B2},F_{c}\}$ $\{F_{B2},T_{c}\}$
        - $\{F_h,T_{B1}\}$
        - $\{F_h,T_{B2}\}$
        - $\{T_h,F_{B1},F_{B2}\}$



    - reason for $a=\top$: $\{F_{B1},T_{b1},F_{a}\}$*

        Since there is a false body $F_{B1}$ in the nogood, then is a constraint like inference to obtain $a$. We then need to get the reason for the body:

        $B1=\bot$
        $\{F_h,T_{B1}\}$
        This is internal so is not liked to a rule

        Putting the nogoods together using resolution we get the reasons for $a$
        $\{F_{h},T_{b1},F_{a}\}$*

        *"Is true $a$ because $h$ is false and $b1$ is true. With rule `h :- not a, b1.` doing a constraint like inference"*

        $G= h\to a, b1\to a$










![Alt text](./img/constraint_like.svg)


- **Last supporting rule**

    If `a` is true and for all rules $r$ such that $a\in H(r)$
    if $\exists_{i}$ such that $ \forall_{j \neq i}\;B(r_j)$ is false.
    - Then $B(r_i)$ must be true

    *Example*

    - `a:-b1.`
      `a:-b2.`

        **`a ~b1` $\to$ `b2`**

![Alt text](./img/last_supporting_rule.svg)

- **Well founded**

    Not considered
    Maybe we could say that anything that is not explained using the inferences above, came from well founded.

------------------------------------------------------------


### Meta-encoding implementing inference rules

The encoding `inf_meta.lp` file implements the inference rules listed above.

In order to work with it, we need the logic program used during minimum
core computation in a reified form. Additionally, we also give the literals
found in the core as input.

Here is a sample run:

```bash
$ clingo --output=reify  ex1.lp | clingo - inf_meta.lp core.lp -c i=3
clingo version 5.6.2
Reading from - ...
Solving...
Answer: 1
true(a,1,avoid_inconsistency) true(b,2,support) true(__mus__,3,support)
SATISFIABLE
```

Note that `inf_meta.lp` encodes inference rules as actions applied in order similar
to a planning problem. The goal is to generate the query. The number of these inference
rule applications is given via the constant `i`, similar to the horizon in a planning problem.

## TODOS

### New pipeline

(Susana)
- Pm = P + Add __mus_directives 
- Ph = P + [{a} for a in query + answer set] 
- h = Compute herbrand base of Ph
- Px = Pm + Add #external a for a in h 
- S = Get Selectors (Px)

- Pw = Px.decouple rules (Hannes)
    ```
    % a(X):- b(X); c(Y); __mus__(program,0).
    body("a(X):-b(X) c(Y). base64",(X,Y)):- b(X); c(Y); __mus__(program,0).
    a(X):-body(_,(X,Y)).
    ```
- R = Reify Pw
- M = Meta of R + S (Orkunt)
- G = Meta to build graph based on R + S + M  (Susana + Hannes + Orkunt)


### Complex development

#### Clasp
- Build and run locally
- Fork clasp and clingo to get our own version
- Print the internal program of clasp into a file
- [ ] How to know were certain literals come from (Body, auxiliary)
  - We need to add hack into clasp and output this information
- [ ] Link body variables and nogoods to ground rules
  - This is not a one to one correspondence since the set of nogoods is a set so an element might come from more than one rule.

#### Gringo
- [ ] Link grounded rules to non-ground rules
  - We can add a theory atom with the line number of every rule (Hannes)


### Meta-encoding for inference rules

- [ ] Integration with ucorexplain
- [ ] Some encoding improvements
- [ ] Incremental version
- [ ] Generating an explanation graph from the inference plan
- [ ] Extending inference rules for choice rules and aggregates

### Multiple queries
- [ ] Revisit Semantic for multiple  queries
- [ ] All queries in the same rule `stop:- q1,q2,....`
- [ ] Propagator to look for `stop` and stop the propagation by propagating `~stop`
- [ ] Keep the `not true` in the assumptions
- [ ] Use the propagator also in the unit propagation to get the proof tree


### Example application
- [ ] Write sudoku with disjunction in the head and without choices (Hannes)
- [ ] Add the proof tree expected output in tests (Copy from mail)
- [ ] Add more tests based on the different inferences

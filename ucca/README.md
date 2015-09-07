`ucca` package
====================

List of Modules
---------------
1. `classify` -- provides interface to `sklearn`, `mlpy` and `numpy` which
enable training and evaluation of binary classifications related to UCCA
2. `collins` -- provides objects and parsing of Collins dictionary format
3. `convert` -- provides functions to convert between the UCCA objects (pythonic)
to site annotation XML, standard XML representation and text
4. `core` -- provides the basic objects of UCCA relations: `Node`, `Edge`, `Layer`
and Passage, which are the basic items to work with
5. `features` -- provides feature extraction from raw text
6. `layer0` -- provides the text layer (layer 0) objects: `Layer0` and `Terminal`
7. `layer1` -- provides the foundational layer objects: `Layer1`, `FoundationalNode`,
`PunctNode` and `Linkage`
8. `lex` -- provides lexical utilities
9. `postags` -- provides basic POS tags
10. `scenes` -- provides utilities to extract and classify scenes and scene heads
11. `token_eval` -- provides utilities to evaluate token classification
12. `util` -- provides `break2sentences` (of a passage, based on annotation)
13. `wikt` -- provides wiktionary-related functionality

In addition, a `tests` package is present, enabling unit-testing.

Author
------
Amit Beka: amit.beka@gmail.com
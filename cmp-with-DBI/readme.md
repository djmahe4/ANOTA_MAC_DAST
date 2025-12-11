# Comparison with DBI Frameworks

Anota is fundamentally different from general-purpose DBI frameworks like Valgrind [valgrind](https://valgrind.org/) and DynamoRIO [dynamorio](https://dynamorio.org/). While all are frameworks developed for dynamic analysis, they are not competing technologies. As summarized in Table VI in the paper, they are complementary tools with starkly different designs, target users, and objectives.

## Fundamental Design Difference
The core design of Anota is that of a sanitizer framework. Its purpose is to provide an intuitive and user-friendly system for application developers to define and enforce application-specific security policies directly in the source code.

In contrast, Valgrind and DynamoRIO are machine-code instrumentation platforms. They are designed for tool-builders and systems programmers. Their purpose is to provide a comprehensive, low-level API to monitor and modify a program's binary instruction stream at runtime, enabling the creation of a wide range of custom binary analysis tools (e.g., profilers, memory checkers) that operate on binary executables.

## Interfaces and Ease of Use
The intended user of each framework dictates its interface. For Anota, the user is the application developer or security analyst. The interface consists of high-level, function-like annotations embedded directly in the source code. The task is policy definition, not systems programming to implement program analysis tools. The user does not need to know the internal details of Anota.

For DBI frameworks, the user is a tool-builder who must implement analysis logic using complex APIs provided by the frameworks. This interface provides powerful, low-level abstractions, such as Valgrind's ISA-independent Intermediate Representation (IR) or DynamoRIO's direct machine instruction stream manipulation, but requires deep expertise in the framework's internal architecture. Then the user can leverage such powerful APIs to further develop analysis tools.

## Vulnerability Detection Capabilities
The frameworks themselves do not detect vulnerabilities as they provide the mechanisms that enable the vulnerability detection. Anota as a sanitizer specifically designed for business-logic vulnerabilities, does not target low-level errors supported by pre-built tools shipped with Valgrind/DynamoRIO. The DBI frameworks, by design, are more general, can theoretically detect business-logic vulnerabilities but requiring additional expertise and engineering effort from the user to implement specialized tools.

For Anota, as a sanitizer framework, enforces the semantic policies defined by its annotation interface. It is therefore designed to detect violations of business-logic vulnerabilities. Valgrind, however, has a different goal, it's core capability is lifting binary code to an IR and providing support for shadow values. This design enables the creation of tools that detect violations of universal execution rules like memory safety (e.g., MemCheck) or threading rules (e.g., Helgrind). Similarly, DynamoRIO's core capability is providing a fast, fine-grained, and robust API for any manipulation of the machine instruction stream. 
This general-purpose design enables a vast range of tools which are mostly designed to find low-level execution errors like Dr.Memory for memory related errors. The rich APIs provided make it possible to further implement binary analysis tools to detect business-logic vulnerabilities.

## Limitations of Implementing Anota Using DBI Frameworks
While one might theoretically attempt to implement Anota's functionality on a DBI framework, it is practically infeasible due to the semantic gap. To support a language like Python, DBI frameworks operate on the compiled, machine-code binary of the CPython interpreter, not the high-level application logic it is executing. They are blind to the application's semantic context.

For example, consider Anota's annotation `EXECUTION.BLOCK (user.type!='admin')`.
Via inernal interpreter instrumentation, Anota has direct native access to the user object and its type attribute. It operates at the application's semantic level. A DBI tool, in contrast, would see only the `mov`, `cmp`, and `je` machine instructions of the CPython interpreter's binary. It has no direct concept of a user object. To acquire this information, the DBI tool would have to monitor all memory accesses and attempt to reverse-engineer the CPython interpreter's memory layout to map raw addresses to Python run-time objects. This approach is inefficient and unreliable.

Similarly, a DBI-based taint tracker is semantically blind. It can track data flow from memory address A to B, but it lacks the developer-provided intent to know that the variable `pwd` at address A is sensitive and the function print at address B is a dangerous sink in this specific context. Furthermore, [known incompatibilities](https://svn.python.org/projects/python/trunk/Misc/valgrind-python.supp) between CPython's custom memory allocator and tools like Memcheck can introduce a high rate of false positives.

## Performance Overhead and Design Tradeoffs
The semantic gap is not the only barrier. The performance overhead of a DBI-based approach would be prohibitive. 
Same as the benchmark suited used in the performance evaluation, we use [The Python Performance Benchmark Suite](https://github.com/python/pyperformance) which is designed to be an authoritative source of benchmarks for all Python implementations and focuses on real-world benchmarks with 87 different tasks in total. 
We evaluated the cost of monitoring all memory accesses, a necessary prerequisite for the reverse-engineering to map the memory to runtime objects. 
This monitoring introduces a runtime overhead of 5417% (54.17x) with DynamoRIO's memory trace, 5513% (55.13x) with Valgrind's Memcheck. Detailed results are in the below Table. 
Additionally, we assess a memory tracing tool based on a slimmed down version of [Valgrind's Lackey tool](https://valgrind.org/docs/manual/lk-manual.html) with an overhead of 8756% (87.56x). 
This exceeds Memcheck's overhead, as Lackey prioritizes implementation clarity over performance. These results suggest that DBI-based implementations will have high overhead and developing them requires substantial expertise regarding the framework's internals.

This overhead is a direct result of different design tradeoffs. Anota trades generality (having source / interpreter access) for performance and semantic awareness.
Our current prototype is built on top of standard Python interpreters for the projects with source code available, the instrumented code can directly monitor and manipulate the Python run-time events from the internal perspective without need of inefficient reverse-engineering.
Its lightweight, targeted mechanisms are activated only when and where a specific event is triggered (e.g., annotation enable), resulting in a overhead of about 10%. 
DBI frameworks trade performance for capability and generality. Their heavyweight, JIT-based architecture is extremely expensive while they can run on any binaries. 
Moreover, they serve as a base framework providing rich APIs to the tool-builders, those tool-builders could future extend the functionalities by developing new tools using their knowledge on the DBI frameworks and target problems.

While one could apply Anota's concepts using DBI frameworks, the performance penalty makes it impractical for tasks like fuzzing, which rely on repeated program execution. 
A more suitable use case for a DBI-based approach would be in single-run analyses, such as verifying a specific exploit on a binary-only target, where performance is not the primary concern.


| Benchmark| DynamoRio Memtrace| Valgrind Memcheck| 
|-----------------------------|---------|---------|
| 2to3                        | 67.58x  | 60.32x  |
| async\_generators           | 58.36x  | 52.27x  |
| async\_tree\_cpu\_io\_mixed | 38.20x  | 49.46x  |
| async\_tree\_io             | 35.21x  | 41.62x  |
| async\_tree\_memoization    | 41.47x  | 49.05x  |
| async\_tree\_none           | 42.17x  | 51.27x  |
| asyncio\_tcp                | 48.00x  | 28.21x  |
| asyncio\_tcp\_ssl           | 67.76x  | 117.77x |
| asyncio\_websockets         | 24.87x  | 23.09x  |
| bench\_mp\_pool             | 7.42x   | 13.08x  |
| bench\_thread\_pool         | 10.31x  | 11.11x  |
| chameleon                   | 39.15x  | 39.51x  |
| chaos                       | 81.61x  | 75.68x  |
| comprehensions              | 93.11x  | 91.65x  |
| coroutines                  | 91.68x  | 57.53x  |
| coverage                    | 47.21x  | 29.66x  |
| create\_gc\_cycles          | 5.85x   | 10.39x  |
| crypto\_pyaes               | 70.05x  | 86.85x  |
| deepcopy                    | 80.66x  | 78.61x  |
| deepcopy\_memo              | 73.91x  | 55.61x  |
| deepcopy\_reduce            | 81.87x  | 86.15x  |
| deltablue                   | 85.54x  | 63.20x  |
| django\_template            | 82.05x  | 79.49x  |
| docutils                    | 48.75x  | 54.29x  |
| dulwich\_log                | 45.73x  | 56.80x  |
| fannkuch                    | 76.17x  | 60.84x  |
| float                       | 63.45x  | 58.90x  |
| gc\_traversal               | 13.18x  | 23.28x  |
| generators                  | 50.76x  | 39.89x  |
| genshi\_text                | 80.53x  | 73.58x  |
| genshi\_xml                 | 73.35x  | 68.65x  |
| go                          | 76.82x  | 61.44x  |
| hexiom                      | 93.22x  | 70.65x  |
| html5lib                    | 56.77x  | 57.91x  |
| json\_dumps                 | 60.70x  | 73.67x  |
| json\_loads                 | 50.30x  | 64.91x  |
| logging\_format             | 80.75x  | 79.81x  |
| logging\_silent             | 76.86x  | 41.93x  |
| logging\_simple             | 81.06x  | 77.94x  |
| mako                        | 68.19x  | 65.13x  |
| mdp                         | 50.07x  | 61.03x  |
| meteor\_contest             | 47.84x  | 45.03x  |
| nbody                       | 69.54x  | 42.85x  |
| nqueens                     | 81.32x  | 76.24x  |
| pathlib                     | 51.38x  | 72.21x  |
| pickle                      | 56.46x  | 57.44x  |
| pickle\_dict                | 28.73x  | 37.78x  |
| pickle\_list                | 34.81x  | 42.45x  |
| pickle\_pure\_python        | 85.54x  | 80.77x  |
| pidigits                    | 20.56x  | 17.31x  |
| pprint\_pformat             | 76.60x  | 86.75x  |
| pprint\_safe\_repr          | 76.64x  | 85.50x  |
| pyflate                     | 67.10x  | 68.45x  |
| python\_startup             | 105.31x | 87.27x  |
| python\_startup\_no\_site   | 104.39x | 93.65x  |
| raytrace                    | 84.78x  | 72.12x  |
| regex\_compile              | 64.77x  | 67.60x  |
| regex\_dna                  | 14.98x  | 21.82x  |
| regex\_effbot               | 26.74x  | 54.05x  |
| regex\_v8                   | 35.75x  | 39.93x  |
| richards                    | 88.48x  | 62.94x  |
| richards\_super             | 87.64x  | 71.53x  |
| scimark\_fft                | 67.00x  | 68.97x  |
| scimark\_lu                 | 84.31x  | 68.15x  |
| scimark\_monte\_carlo       | 84.31x  | 81.36x  |
| scimark\_sor                | 91.47x  | 82.54x  |
| scimark\_sparse\_mat\_mult  | 41.59x  | 51.37x  |
| spectral\_norm              | 70.31x  | 74.82x  |
| sqlalchemy\_declarative     | 43.19x  | 48.89x  |
| sqlalchemy\_imperative      | 45.89x  | 53.00x  |
| sqlite\_synth               | 85.72x  | 93.92x  |
| sympy\_expand               | 65.94x  | 73.24x  |
| sympy\_integrate            | 56.56x  | 60.65x  |
| sympy\_str                  | 62.08x  | 69.54x  |
| sympy\_sum                  | 55.87x  | 66.06x  |
| telco                       | 79.13x  | 107.09x |
| tomli\_loads                | 67.40x  | 64.18x  |
| tornado\_http               | 34.50x  | 37.21x  |
| typing\_runtime\_protocols  | 70.05x  | 69.38x  |
| unpack\_sequence            | 21.81x  | 21.68x  |
| unpickle                    | 45.03x  | 62.96x  |
| unpickle\_list              | 36.15x  | 50.36x  |
| unpickle\_pure\_python      | 92.98x  | 83.95x  |
| xml\_etree\_generate        | 78.27x  | 84.38x  |
| xml\_etree\_iterparse       | 57.67x  | 57.57x  |
| xml\_etree\_parse           | 47.09x  | 57.45x  |
| xml\_etree\_process         | 78.95x  | 80.96x  |

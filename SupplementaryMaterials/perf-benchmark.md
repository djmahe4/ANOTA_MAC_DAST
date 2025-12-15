# Performance Evaluation

The runtime performance measurement has two different setups. One is *Trace All* that taints all the variables and the other is *Monitor Syscall* that inspects all the system calls. 
Both setups are extreme setups because typical usages only need to inspect a subset of variables or system calls while executing the annotated code. 
The selected benchmark is [the Python Performance Benchmark Suite](https://github.com/python/pyperformance) provided by the CPython developers, which is intended to be an authoritative source of benchmarks for all Python implementations.
We run all the benchmarks in rigorous mode to get more accurate results, the evaluation result is shown in the below Table.

The *Total* shows the name of each subtask.
*Baseline* data is collected from an original, uninstrumented CPython interpreter, and the columns *Monitor Syscall* and *Trace All* are the overhead relative to the baseline execution.
As expected for our run-time performance optimization design choices, the average run-time performance overhead is relatively low, considering the benchmark is evaluated on extreme tracking-everything scenarios.
The overhead introduced by the system call monitor module is 5% in average.

Among the test suites, `bench_mp_pool` and `bench_thread_pool` have a high overhead of around 35% because the benchmark keeps using thread- and process-related system calls.
Similarly, `tornado_http` has 44% overhead because it sets up a server and invokes network-related system calls without other executions, so the overhead is much higher.
Comparing `logging_silent` with `logging_simple` and `logging_format`, the latter have much higher overhead (29% and 118% compared to 1%).
This is caused by writing log data to disk using the `write` system call, while `logging_silent` keeps the log in memory without invoking system calls.
Our system call module inspects every byte written out by the `write` system call, hence the overhead is much higher.

For the *Trace All* scenario, the average overhead is 10%.
The test cases `sync_tree_none`, `async_tree_memoization`, `unpack_sequence` and `bench_mp_poo` have more variables and byte code execution to track, so they have more overhead than other test cases.
Compared with Python dynamic analysis frameworks DynaPyt [eghbali2022dynapyt], which incurs an overhead between 1.2x and 16x as evaluated by their paper, Anota has a much lower performance impact.
We attribute this to the instrumentation and tracking of Anota happening inside the interpreter, while DynaPyt's instrumentation is implemented as an external module in Python.


|Benchmark|Baseline Time /ms|Monitor Syscall (ms)| Monitor Syscall Overhead|Trace All Time (ms)|Trace All Overhead|
|-----------------------------|--------------------|---------------|-------|-----------------|------|
| Total                    | 15039.277443399998 | 15721.4414742 | 5%   | 16494.179284809 | 10% |
| 2to3                        | 174                | 188           | 8%   | 189.66          | 9%  |
| async_generators           | 197                | 208           | 6%   | 218.67          | 11% |
| sync_tree_none            | 357                | 382           | 7%   | 431.97          | 21% |
| async_tree_cpu_io_mixed | 495                | 532           | 7%   | 598.95          | 21% |
| async_tree_io             | 855                | 935           | 9%   | 974.7           | 14% |
| async_tree_memoization    | 430                | 451           | 5%   | 533.2           | 24% |
| asyncio_tcp                | 360                | 437           | 21%  | 367.2           | 2%  |
| asyncio_tcp_ssl           | 1470               | 1600          | 9%   | 1484.7          | 1%  |
| asyncio_websockets         | 163                | 175           | 7%   | 164.63          | 1%  |
| chameleon                   | 4.94               | 5.16          | 4%   | 5.4834          | 11% |
| chaos                       | 57                 | 59.1          | 4%   | 62.13           | 9%  |
| comprehensions              | 0.0155             | 0.016         | 3%   | 0.016895        | 9%  |
| bench_mp_pool             | 3.85               | 5.11          | 33%  | 4.697           | 22% |
| bench_thread_pool         | 0.541              | 0.752         | 39%  | 0.60051         | 11% |
| coroutines                  | 15.5               | 15.5          | 0%   | 16.895          | 9%  |
| coverage                    | 27.2               | 27.5          | 1%   | 29.104          | 7%  |
| crypto_pyaes               | 62.9               | 64.1          | 2%   | 69.19           | 10% |
| dask                        | 212                | 253           | 19%  | 212             | 0%  |
| deepcopy                    | 0.241              | 0.252         | 5%   | 0.26751         | 11% |
| deepcopy_reduce            | 0.00223            | 0.00227       | 2%   | 0.002453        | 10% |
| deepcopy_memo              | 0.0265             | 0.027         | 2%   | 0.02915         | 10% |
| deltablue                   | 3.87               | 4.05          | 5%   | 4.1022          | 6%  |
| django_template            | 27.5               | 28            | 2%   | 29.975          | 9%  |
| docutils                    | 1630               | 1660          | 2%   | 1939.7          | 19% |
| dulwich_log                | 38.9               | 49.9          | 28%  | 40.845          | 5%  |
| fannkuch                    | 248                | 249           | 0%   | 280.24          | 13% |
| float                       | 56.3               | 58.1          | 3%   | 65.308          | 16% |
| create_gc_cycles          | 0.756              | 0.765         | 1%   | 0.77112         | 2%  |
| gc_traversal               | 1.83               | 1.84          | 1%   | 1.8483          | 1%  |
| generators                  | 26.7               | 26.7          | 0%   | 27.234          | 2%  |
| genshi_text                | 16.9               | 17            | 1%   | 18.928          | 12% |
| genshi_xml                 | 32.7               | 32.3          | -1%  | 35.643          | 9%  |
| go                          | 127                | 127           | 0%   | 138.43          | 9%  |
| hexiom                      | 5.15               | 5.12          | -1%  | 5.562           | 8%  |
| html5lib                    | 43.3               | 44            | 2%   | 45.465          | 5%  |
| json_dumps                 | 7.38               | 7.49          | 1%   | 7.8228          | 6%  |
| json_loads                 | 0.0128             | 0.013         | 2%   | 0.013568        | 6%  |
| logging_format             | 0.00286            | 0.00624       | 118% | 0.0031174       | 9%  |
| logging_silent             | 0.0000973          | 0.0000981     | 1%   | 0.000104111     | 7%  |
| logging_simple             | 0.00453            | 0.00584       | 29%  | 0.0049377       | 9%  |
| mako                        | 8.35               | 8.61          | 3%   | 9.1015          | 9%  |
| mdp                         | 1660               | 1680          | 1%   | 1693.2          | 2%  |
| meteor_contest             | 63.8               | 66.2          | 4%   | 67.628          | 6%  |
| nbody                       | 64.8               | 68.1          | 5%   | 78.408          | 21% |
| nqueens                     | 58.8               | 59.7          | 2%   | 62.328          | 6%  |
| pathlib                     | 10.4               | 17.5          | 68%  | 11.024          | 6%  |
| pickle                      | 0.00546            | 0.00561       | 3%   | 0.005733        | 5%  |
| pickle_dict                | 0.0167             | 0.0176        | 5%   | 0.01837         | 10% |
| pickle_list                | 0.0023             | 0.00231       | 0%   | 0.002369        | 3%  |
| pickle_pure_python        | 0.245              | 0.259         | 6%   | 0.26705         | 9%  |
| pidigits                    | 109                | 114           | 5%   | 110.09          | 1%  |
| pprint_safe_repr          | 567                | 594           | 5%   | 618.03          | 9%  |
| pprint_pformat             | 1170               | 1180          | 1%   | 1275.3          | 9%  |
| pyflate                     | 349                | 355           | 2%   | 380.41          | 9%  |
| python_startup             | 5.49               | 6.58          | 20%  | 5.7096          | 4%  |
| python_startup_no_site   | 3.56               | 4.3           | 21%  | 3.7024          | 4%  |
| raytrace                    | 271                | 277           | 2%   | 287.26          | 6%  |
| regex_compile              | 94.4               | 95.1          | 1%   | 102.896         | 9%  |
| regex_dna                  | 110                | 112           | 2%   | 113.3           | 3%  |
| regex_effbot               | 1.52               | 1.55          | 2%   | 1.5808          | 4%  |
| regex_v8                   | 12.9               | 12.9          | 0%   | 13.029          | 1%  |
| richards                    | 41                 | 41.3          | 1%   | 45.51           | 11% |
| richards_super             | 48.7               | 51.1          | 5%   | 52.109          | 7%  |
| scimark_fft                | 191                | 199           | 4%   | 212.01          | 11% |
| scimark_lu                 | 90.3               | 93.4          | 3%   | 96.621          | 7%  |
| scimark_monte_carlo       | 57.6               | 58            | 1%   | 63.36           | 10% |
| scimark_sor                | 105                | 105           | 0%   | 112.35          | 7%  |
| scimark_sparse_mat_mult  | 3.04               | 3.08          | 1%   | 3.344           | 10% |
| spectral_norm              | 78.2               | 78.1          | 0%   | 86.02           | 10% |
| sqlalchemy_declarative     | 83.2               | 86            | 3%   | 88.192          | 6%  |
| sqlalchemy_imperative      | 11                 | 11.1          | 1%   | 11.44           | 4%  |
| sqlglot_normalize          | 193                | 196           | 2%   | 206.51          | 7%  |
| sqlglot_optimize           | 37.3               | 37.7          | 1%   | 40.657          | 9%  |
| sqlglot_parse              | 1.1                | 1.12          | 2%   | 1.199           | 9%  |
| sqlglot_transpile          | 1.32               | 1.35          | 2%   | 1.4256          | 8%  |
| sqlite_synth               | 0.00152            | 0.00153       | 1%   | 0.0015504       | 2%  |
| sympy_expand               | 308                | 311           | 1%   | 323.4           | 5%  |
| sympy_integrate            | 13.6               | 13.7          | 1%   | 14.688          | 8%  |
| sympy_sum                  | 96.8               | 97.8          | 1%   | 102.608         | 6%  |
| sympy_str                  | 180                | 183           | 2%   | 194.4           | 8%  |
| telco                       | 3.81               | 3.86          | 1%   | 4.0767          | 7%  |
| tomli_loads                | 1490               | 1520          | 2%   | 1683.7          | 13% |
| tornado_http               | 69.6               | 100           | 44%  | 73.08           | 5%  |
| typing_runtime_protocols  | 0.313              | 0.314         | 0%   | 0.33178         | 6%  |
| unpack_sequence            | 0.0000261          | 0.0000261     | 0%   | 0.000030798     | 18% |
| unpickle                    | 0.0076             | 0.00764       | 1%   | 0.00798         | 5%  |
| unpickle_list              | 0.00232            | 0.00231       | 0%   | 0.0023664       | 2%  |
| unpickle_pure_python      | 0.171              | 0.172         | 1%   | 0.18639         | 9%  |
| xml_etree_parse           | 77                 | 77.1          | 0%   | 81.62           | 6%  |
| xml_etree_iterparse       | 53                 | 54.6          | 3%   | 56.18           | 6%  |
| xml_etree_generate        | 50.3               | 51.9          | 3%   | 53.318          | 6%  |
| xml_etree_process         | 43.1               | 43.1          | 0%   | 46.548          | 8%  |

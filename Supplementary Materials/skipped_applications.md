# Skipped Applications

As mentioned in our evaluation section, several packages were excluded from our experiment due to various limitations; these packages are listed in the below Table. 

We skipped packages if: 

(1) we lacked the necessary domain knowledge for analysis (e.g., understanding the Qdrant API for qdrant-client or cryptographic algorithms for Cryptography); 

(2) we encountered unsatisfied requirements, often due to environment constraints (like lacking the required GPU setup for llama-cpp-python); 

(3) the package used multiple languages, including some not supported by our current prototype;

(4) the package functions primarily as a third-party library or plugin without clear entry points for the users (such as the pytest-cov testing plugin or the Transformers deep learning library).



| **ID** | **Name**                                                                 | **Stars** | **Vuln. Identifier**    | **LoC**    | **Reason**        |
|--------|--------------------------------------------------------------------------|-----------|-------------------------|------------|-------------------|
|        |                                                                          | / 10^3    |                         | / 10^3     |                   |
| 1      | [qdrant-client](https://github.com/qdrant/qdrant-client)                 | 918       | CVE-2024-3829           | 67260      | Lack Knowledge    |
| 2      | [lemur](https://github.com/Netflix/lemur)                                | 1700      | SNYK-7210298            | 37335      | Lack Knowledge    |
| 3      | [AIT-Core](https://github.com/NASA-AMMOS/AIT-Core)                       | 46        | CVE-2024-35058          | 17790      | Lack Knowledge    |
| 4      | [cryptography](https://github.com/pyca/cryptography)                     | 7000      | CVE-2024-4603           | 56674      | Lack Knowledge    |
| 5      | [llama-cpp-python](https://github.com/abetlen/llama-cpp-python)          | 8900      | CVE-2024-34359          | 14405      | Missing HW Req.   |
| 6      | [aliyundrive-webdav](https://pypi.org/project/aliyundrive-webdav/)       | 9700      | CVE-2024-29640          | 162        | Unsupported Lang. |
| 7      | [pytest-cov](https://github.com/pytest-dev/pytest-cov)                   | 1800      | SNYK-6514860            | 2810       | Unclear Entry Pt. |
| 8      | [idna](https://github.com/kjd/idna)                                      | 256       | SNYK-6597975            | 14459      | Lack Knowledge    |
| 9      | [transformers](https://github.com/huggingface/transformers)              | 142000    | CVE-2023-6730           | 1188188    | Unclear Entry Pt. |
| 10     | [manim-studio](https://github.com/MathItYT/manim-studio)                 | 76500     | SNYK-6141258            | 1450       | Lack Knowledge    |
| 11     | [specter-desktop](https://github.com/cryptoadvance/specter-desktop)      | 823       | SNYK--6840403           | 39989      | Lack Knowledge    |
| 12     | [keras](https://github.com/keras-team/keras)                             | 62800     | CVE-2024-3660           | 195486     | Lack Knowledge    |

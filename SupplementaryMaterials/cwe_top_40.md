
# An analysis of Anota's support for the CWE Top 40 Security Weaknesses.

- "✓": Supported vulnerability classes.
- "🛠": Vulnerabilities where an annotation system is not useful, as they can be directly patched if the developer has the co1w3e4r tgyhjkl;-0-0-=-*9/8rect intuition.
- "📖": Classes supported by complimentary tools. This existing work is listed in the last column, even though these tools mostly focus on technical, non-business logic-related issues.

Business Logic Needed (BLN) refers to whether the bugs can only be found with an understanding of the application's business logic:
- ●: Required
- ○: Not required
- ◐: Partially required (only some bugs require this understanding)


| **Rank** | **CWE** | **Description** | **Exploitation** | **BLN** | **Anota** | **Existing Work** |
| :--- | :--- | :--- | :--- | :---: | :---: | :--- |
| 1 | 79 | Cross-site Scripting | APP Data | ○ | 📖 | FuzzOrigin [281314fuzzorigin], KameleonFuzz [KameleonFuzz], webFuzz [webfuzz] |
| 2 | 787 | Out-of-bounds Write | Memory | ○ | 📖 | ASan [serebryany_addresssanitizer_2012] |
| 3 | 89 | SQL Injection | DataBase | ○ | 📖 | Witcher [witcher], Atropos [Atropos] |
| 4 | 352 | Cross-Site Request Forgery (CSRF) | System Call | ◐ | 🛠 | WebFuzzAuto [csrffuzz] |
| 5 | 22 | Path Traversal | System Call | ● | ✓ | Atropos [Atropos], PHUZZ [PHUZZ] |
| 6 | 125 | Out-of-bounds Read | Memory | ○ | 📖 | ASan [serebryany_addresssanitizer_2012] |
| 7 | 78 | OS Command Injection | System Call | ◐ | ✓ | Witcher [witcher], Atropos [Atropos] |
| 8 | 416 | Use After Free | Memory | ○ | 📖 | ASan [serebryany_addresssanitizer_2012] |
| 9 | 862 | Missing Authorization | Object Access/Code Exec. | ● | ✓ |  |
| 10 | 434 | Unrestricted Upload of File | System Call | ◐ | ✓ | Atropos [Atropos], UFuzzer [ufuzzer], URadar [URadar] |
| 11 | 94 | Code Injection | System Call/Data Flow | ◐ | ✓ |  |
| 12 | 20 | Improper Input Validation | System Call | ◐ | 🛠 | Witcher [witcher], Atropos [Atropos] |
| 13 | 77 | Command Injection | System Call | ◐ | ✓ | Witcher [witcher], Atropos [Atropos] |
| 14 | 287 | Improper Authentication | Object Access/Code Exec. | ● | ✓ |  |
| 15 | 269 | Improper Privilege Management | Object Access/Code Exec. | ● | ✓ |  |
| 16 | 502 | Deserialization of Untrusted Data | System Call | ● | ✓ | \DFuzz [ODDFuzz], PHUZZ [PHUZZ] |
| 17 | 200 | Exposure of Sensitive Information | Data Flow/System Call | ● | ✓ | EDEFuzz [edefuzz], FLOWFUZZ [infoflowfuzz] |
| 18 | 863 | Incorrect Authorization | Object Access/Code Exec. | ● | ✓ |  |
| 19 | 918 | Server-Side Request Forgery (SSRF) | System Call | ◐ | ✓ | Atropos [Atropos], SSRFuzz [SSRFuzz] |
| 20 | 119 | Improper Restriction of Ops. w/i Mem. Buffer | Memory | ○ | 📖 | ASan [serebryany_addresssanitizer_2012] |
| 21 | 476 | NULL Pointer Dereference | Memory | ○ | 📖 | ASan [serebryany_addresssanitizer_2012] |
| 22 | 798 | Use of Hard-coded Credentials | Data | ● | 🛠 |  |
| 23 | 190 | Integer Overflow or Wraparound | Memory | ○ | 📖 | UBSan [undefinedbehaviorsanitizer_2013] |
| 24 | 400 | Uncontrolled Resource Consumption | DOS | ○ | ✓ | All Fuzzers |
| 25 | 306 | Missing Authentication for Critical Function | Object Access/Code Exec. | ● | ✓ |  |
| 26 | 770 | Allocation of Resources Without Limit | DOS | ○ | 📖 | All Fuzzers |
| 27 | 668 | Exposure of Resource to Wrong Sphere | Object Access/Code Exec. | ● | ✓ | EDEFuzz [edefuzz] |
| 28 | 74 | Improper Neutralization of Special Elements | System Call/Data Flow | ◐ | ✓ | Witcher [witcher] |
| 29 | 427 | Uncontrolled Search Path Element | System Call | ◐ | ✓ |  |
| 30 | 639 | Authorization Bypass | Object Access/Code Exec. | ● | ✓ |  |
| 31 | 532 | Insertion of Sensitive Information into Log File | Data Flow | ● | ✓ | FLOWFUZZ [infoflowfuzz] |
| 32 | 732 | Incorrect Permission Assignment | Object Access/Code Exec. | ● | ✓ |  |
| 33 | 601 | Open Redirect | System Call | ◐ | ✓ | OpenRedireX [OpenRedireX] |
| 34 | 362 | Race Condition | System Call/Object Access | ◐ | ✓ | TSan [serebryany2009threadsanitizer], CONZZER [CONZZER], krace [krace] |
| 35 | 522 | Insufficiently Protected Credentials | Data Flow/Object Access | ● | ✓ |  |
| 36 | 276 | Incorrect Default Permissions | Object Access/Code Exec. | ● | 🛠 |  |
| 37 | 203 | Observable Discrepancy | Data Flow | ● | ✓ | CT-Fuzz [he2020ct] |
| 38 | 59 | Link Following | System Call | ○ | 🛠 |  |
| 39 | 843 | Type Confusion | Memory | ○ | 📖 | type-san [type-san] |
| 40 | 312 | Cleartext Storage of Sensitive Information | Data Flow | ○ | 📖 |  |
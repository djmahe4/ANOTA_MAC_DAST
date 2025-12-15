# Annotation Study Details

A total of 15 participants initially expressed interest in joining the study. However, 4 were excluded because they were first- or second-year undergraduate students with no reported knowledge of application development or security analysis. This background was deemed too distant from Anota's target users, who are application developers and security analysts.
The 11 participants, referred to as P1--P11, were computer science undergraduate and graduate students with varying levels of expertise in application development and security.
Among them, P1--P2 had hands-on experience with security vulnerabilities and a basic understanding of application development.
P3--P5 were experts in security vulnerabilities with basic knowledge of application development.
P6--P8 had practical experience with web applications and a basic understanding of security vulnerabilities.
Lastly, P9--P11 possessed only a basic conceptual understanding of application development, with no prior knowledge of security vulnerabilities.
All of them do not have any prior experience with Anota or familiarity with the target code bases used in the study.
Each participant was tasked with annotating six randomly selected vulnerable applications.
For each participant, we recorded the number of annotations added and the time it took to complete the task. Furthermore, we analyzed the effectiveness of the added annotations.
Moreover, we collected knowledge-level information and feedback from the participants.


## Preparation
As the participants are unfamiliar with the applications, contrary to a developer who would use Anota, the participants are given the following information for the study: a summary of the application's main purpose as initial guidance, instructions on using Anota including the syntax of the potential annotations, and example annotations for each type of vulnerability.
Furthermore, we provide information on common code patterns associated with each vulnerability type to help them understand these classes of vulnerabilities.
To help them better understand where to add annotations, we instructed participants can begin with identifying security-critical boundaries where data crosses trust domains.
We advised them that effective annotations are often derived from sources like documentation or API specifications to verify if a behavior is intended.
Note that we avoided giving details about specific APIs or internal application knowledge from the applications used in the user study to prevent leaking hints to the participants.
No information about the existing vulnerabilities is given to the participants.
The full instruction document will be published as part of our research artifact in the anonymous repository.


## Participant Feedback
Participants were asked to provide feedback after completing their assignments and to self-report their knowledge levels. The key takeaways from their feedback are summarized as follows: Concerns About Overlooking Critical Annotations: Participants expressed apprehension about potentially missing important locations to annotate, which led them to spend additional time during the initial phase of the process. Preference for Block Lists Over Allow Lists: Participants found it more comfortable and practical to use block lists rather than allow lists, as block lists were easier to construct and reduced the likelihood of false positives. Ease of Learning and Using Annotation Syntax: All participants reported that the syntax of Anota's annotations was straightforward to learn and use.

Nine participants expressed concerns about potentially overlooking critical locations to annotate, leading them to spend considerable time minimizing this risk during the initial phase.
This concern is understandable, as the participants lacked detailed knowledge of the applications under test.
However, this issue is unlikely to arise for developers, who are familiar with the code bases they typically work on, even for large projects.

Ten participants' feedback mentions they were more confident while writing blocklists for system calls compared to writing allowlists.
This outcome was expected, as it is impractical for participants to have comprehensive knowledge of the underlying code.
Using blocklists to constrain code behavior proved to be both easier and effective, enabling participants to identify most vulnerabilities in the applications as shown in Table.
Differently, it is also mentioned that when the code or documentation shows explicit information like constant variables representing that a certain file path or an executable binary could be accessed, participants prefer to use the allowlist since it is more accurate.

All participants found annotation syntax of Anota straightforward to learn and use.
They described an initial learning curve, followed by a systematic approach to annotation.
Participants adopted a strategy of focusing on one annotation type at a time to reduce context switching.
For example, a participant might first identify and annotate sensitive variables (e.g., secrets), then move on to annotate potential system call sites, proceeding sequentially in this manner.
## Failure Cases
P10 failed to write an annotation to detect the sensitive information leakage vulnerability in `WordOps` (10 of the 11 participants succeeded in this task), a WordPress stack management tool set. P10 missed the descriptions of credentials in the WordPress documentation and thus failed to detect this vulnerability.
P9 failed to write an annotation to detect the path traversal in `xtts-api-server` (10 of the 11 participants succeeded in this task) because P9 restricted the wrong file path while using the file access annotation in the correct place.
P11 failed to write an annotation to detect the SSRF in `Gradio` (10 of the 11 participants succeeded in this task) because the participant had a misunderstanding of the SSRF vulnerability.
Regarding `cmdb`, P5 and P8 added more annotations compared to the other two participants.
This is because P5 and P8 add annotations at the beginning of each function protected by the authentication decorator, while the other participants add the annotation inside the decoration function. From a semantic point of view, both approaches are equivalent.

## False Positives
To study the false positive cases, we manually inspect the annotations and show the data in the column FP in Table.
The number of false positives is low, and we find that the following two factors might help reduce the number even further:
the participants tend to write annotations around the code that explicitly express the developer's intention.
For example, annotations are added based on the conditions in the if-statement or a path concatenation which shows the folder the code will operate on.
The participants prefer to use blocklists (over allowlists), which is less likely to cause false positives.

False positives in Anota are commonly associated with system call and data flow annotations.
System call-related false positives often occur within functions that contain a few lines of annotated code, whereas data flow-related false positives may appear in modules different from those where the annotations are made.
In either case, these false positives are straightforward for Anota's target users—application developers—to understand and resolve.
Developers are familiar with the codebase and can address these issues iteratively, refining annotations as needed to eliminate false positives effectively.
Furthermore, since our participants did not have access to the testing results, they could not fix false positives before submitting their annotations.
In reality, adding annotations is an iterative approach, and developers can quickly remove them.



**Usability Study Result (Time is measured in minutes)**

| ID | [Gradio](https://github.com/gradio-app/gradio)<br>(SSRF)<br>Time | Num | (FP) | Result | [xtts-api-server](https://github.com/daswer123/xtts-api-server)<br>(Path Traversal)<br>Time | Num | (FP) | Result | [cmdb](https://github.com/veops/cmdb)<br>(Unrestricted Upload)<br>Time | Num | (FP) | Result | [temporai](https://github.com/vanderschaarlab/temporai)<br>(Untrusted Deserial.)<br>Time | Num | (FP) | Result | [WordOps](https://github.com/WordOps/WordOps)<br>(Information Leakage)<br>Time | Num | (FP) | Result | [changedetection.io](https://github.com/dgtlmoon/changedetection.io)<br>(Broken Access Control)<br>Time | Num | (FP) | Result |
| :--- | :--- | :--- | :--- | :---: | :--- | :--- | :--- | :---: | :--- | :--- | :--- | :---: | :--- | :--- | :--- | :---: | :--- | :--- | :--- | :---: | :--- | :--- | :--- | :---: |
| P1 | 58 | 20 | 1 | ✓ | 21 | 6 | 0 | ✓ | 49 | 3 | 0 | ✓ | 22 | 5 | 0 | ✓ | 20 | 17 | 1 | ✓ | 82 | 23 | 1 | ✗ |
| P2 | 52 | 10 | 2 | ✓ | 22 | 8 | 0 | ✓ | 55 | 12 | 0 | ✓ | 49 | 5 | 0 | ✓ | 45 | 19 | 1 | ✓ | 89 | 19 | 0 | ✗ |
| P3 | 90 | 76 | 4 | ✓ | 10 | 10 | 1 | ✓ | 60 | 46 | 3 | ✓ | 20 | 3 | 0 | ✓ | 60 | 40 | 1 | ✓ | 90 | 68 | 9 | ✓ |
| P4 | 120 | 16 | 0 | ✓ | 30 | 10 | 0 | ✓ | 90 | 10 | 0 | ✓ | 20 | 5 | 0 | ✓ | 75 | 16 | 1 | ✓ | 60 | 8 | 0 | ✓ |
| P5 | 140 | 69 | 2 | ✓ | 43 | 41 | 5 | ✓ | 66 | 127 | 18 | ✓ | 35 | 15 | 0 | ✓ | 93 | 90 | 7 | ✓ | 45 | 64 | 7 | ✗ |
| P6 | 50 | 36 | 0 | ✓ | 30 | 13 | 1 | ✓ | 35 | 72 | 0 | ✓ | 20 | 3 | 0 | ✓ | 65 | 62 | 3 | ✓ | 40 | 16 | 2 | ✓ |
| P7 | 180 | 36 | 3 | ✓ | 80 | 15 | 1 | ✓ | 80 | 76 | 0 | ✓ | 38 | 5 | 1 | ✓ | 70 | 38 | 1 | ✓ | 180 | 93 | 3 | ✓ |
| P8 | 60 | 54 | 0 | ✓ | 40 | 20 | 2 | ✓ | 60 | 123 | 11 | ✓ | 40 | 24 | 3 | ✓ | 35 | 62 | 0 | ✓ | 60 | 69 | 0 | ✗ |
| P9 | 120 | 33 | 2 | ✓ | 30 | 3 | 0 | ✗ | 120 | 61 | 3 | ✓ | 90 | 11 | 0 | ✓ | 90 | 21 | 0 | ✓ | 180 | 69 | 1 | ✗ |
| P10 | 60 | 13 | 0 | ✓ | 30 | 21 | 0 | ✓ | 30 | 23 | 1 | ✗ | 30 | 1 | 0 | ✓ | 30 | 14 | 0 | ✗ | 60 | 13 | 1 | ✗ |
| P11 | 60 | 22 | 1 | ✗ | 40 | 13 | 0 | ✓ | 40 | 17 | 1 | ✓ | 60 | 2 | 0 | ✓ | 150 | 29 | 1 | ✓ | 70 | 5 | 0 | ✗ |
| **Avg.** | 86 | 33 | | | 40 | 15 | | | 62 | 46 | | | 45 | 11 | | | 63 | 28 | | | 80 | 41 | | |
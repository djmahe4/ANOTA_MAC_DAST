import random
import string
import json

class RequestMutator:
    """
    Generates malicious variations of application inputs to trigger logic flaws.
    """
    def __init__(self):
        self.common_tamper_values = [
            "admin", "root", "guest", "0", "1", "-1", "true", "false",
            "null", "NaN", "undefined", "999999", "../../etc/passwd"
        ]

    def mutate_parameters(self, params_dict):
        """
        Applies parameter tampering strategies.
        """
        mutations = []
        
        # 1. Individual parameter replacement
        for key in params_dict.keys():
            for value in self.common_tamper_values:
                mutated = params_dict.copy()
                mutated[key] = value
                mutations.append({
                    "strategy": "parameter_tampering",
                    "target_key": key,
                    "payload": mutated
                })
                
        # 2. Parameter removal (forced browsing / step skipping)
        for key in params_dict.keys():
            mutated = params_dict.copy()
            del mutated[key]
            mutations.append({
                "strategy": "parameter_omission",
                "target_key": key,
                "payload": mutated
            })
            
        return mutations

    def mutate_sequence(self, workflow_steps):
        """
        Applies step-skipping and sequence reordering.
        """
        # Example: [step1, step2, step3] -> [step1, step3]
        mutations = []
        if len(workflow_steps) > 2:
            for i in range(1, len(workflow_steps) - 1):
                skipped = workflow_steps[:i] + workflow_steps[i+1:]
                mutations.append({
                    "strategy": "step_skipping",
                    "skipped_step": workflow_steps[i],
                    "sequence": skipped
                })
        return mutations

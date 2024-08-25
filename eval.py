import os
import json
from resume_comparer import LLMResumeComparer
import concurrent

class Evaluation:
    def __init__(self):
        self.resume_comparer = LLMResumeComparer(resume_folder='test_resumes')
        self.resumes = os.listdir('./test_resumes/ranked')
        self.resumes.sort()

    def batch_comparison(self, comparison_jobs):
        results = []

        with concurrent.futures.ThreadPoolExecutor(max_workers=50) as executor:
            # Submit jobs
            futures = []
            for rank1, rank2 in comparison_jobs:
                resume1, resume2 = self.resumes[rank1], self.resumes[rank2]
                future = executor.submit(self.resume_comparer.compare_resumes, resume1, resume2)
                futures.append(future)

            # Collect the results as they complete
            for future in futures:
                results.append(future.result())
                print("finished a job!")

        return results
    
    def _save_comparisons(self, comparisons):
        with open('test_resumes/comparisons.json') as f:
            data = json.load(f)

        data.extend(comparisons)

        with open('test_resumes/comparisons.json', 'w') as f:
            json.dump(data, f, indent=4)

    def inspect_comparisons(self):
        with open('test_resumes/comparisons.json') as f:
            comparisons = json.load(f)

        for comparison in comparisons:
            if comparison['winner'] != comparison['resume1']:
                self.resume_comparer.pretty_print(comparison)
                input("\nAny key to continue...\n")

    def eval_all(self, min_distance=1, max_distance=None):
        if not max_distance:
            max_distance = len(self.resumes)

        comparison_jobs = []
        for distance in range(min_distance, max_distance):
            for i in range(len(self.resumes) - distance):
                comparison_jobs.append((i, i + distance))

        comparisons = self.batch_comparison(comparison_jobs)
        self._save_comparisons(comparisons)
           
if __name__ == "__main__":
    eval = Evaluation()
    eval.eval_all(min_distance=1, max_distance=3)
    eval.inspect_comparisons()
    
    # from resume_manager import ResumeManager

    # mgr = ResumeManager('test_resumes')
    # mgr.correct_filetypes()


import anthropic
import base64
from random import randint
import os

class LLMResumeComparer:
    PROMPT = """You are an expert software engineering recruiter tasked with comparing two resumes for an early-career software engineering position. Your goal is to analyze both resumes thoroughly and determine which candidate would be a better fit for the role.

Please follow these steps:

1. Carefully review both resumes, paying attention to education, work experience, projects, technical skills, and any other relevant information.

2. For each resume, list the key strengths and potential weaknesses or areas of concern.

3. Compare the resumes based on the following criteria:
   - Relevance and recency of work experience
   - Depth and breadth of technical skills
   - Education and academic performance
   - Project experience and its relevance to software engineering
   - Evidence of problem-solving abilities and initiative
   - Any unique qualities or experiences that stand out

4. Consider how well each candidate's background aligns with typical requirements for an early-career software engineering role.

5. Weigh the pros and cons of each resume, considering which candidate is likely to perform better in the role and have more potential for growth.

6. After thorough analysis and comparison, form your conclusion about which resume you prefer.

7. Explain your reasoning in detail, covering all the points you considered in your decision-making process.

8. Only after providing your complete analysis and reasoning, state your final decision by writing either "I prefer Resume A" or "I prefer Resume B" as the very last line of your response.

Remember, your goal is to provide a comprehensive comparison and justification for your choice before stating your final preference."""

    PROMPTlol = """
You are an expert in hiring and evaluating software engineers. You have two resumes in front of you, and you need to compare them to determine which candidate is more suitable for a software engineering position. Focus on the following aspects of each resume:

1. Professional Experience
Look at the job titles, companies, duration of employment, and key responsibilities.
Assess the relevance and impact of their roles and achievements.

2. Skills and Technologies
Identify the programming languages, tools, frameworks, and technologies each candidate is proficient in.
Evaluate the depth and breadth of their technical skills.

3. Projects
Examine the projects listed, including personal, academic, and professional projects.
Consider the complexity, innovation, and relevance of these projects to the role they are applying for.

4. Education
Review their educational background, including degrees, institutions, and relevant coursework.
Take note of any honors or exceptional academic achievements.

5. Additional Information
Check for any additional skills, languages spoken, certifications, or interests that might be relevant.

6. Overall Impression

At the start, you should only state your reasoning, without stating your final answer. Only at the very end, you MUST state "I prefer Resume A" or "I prefer Resume B".
"""

    PROMPT_alt = """You are an expert technical recruiter at a big tech company looking to hire graduate software engineers. Your task is to evaluate the following two early-career software engineer resumes. Only after discussing your reasoning, state which resume you prefer. You may refer to the resumes as Resume A and Resume B respectively.

Criteria for evaluation:
- Technical depth: how much technical depth and experience does the candidate demonstrate? You should mostly discard non-software engineering experience, e.g. retail or marketing. Furthermore, you must discard A-Level qualifications; they simply do not matter.
- Clarity of communication: is it easy to understand what exactly the candidate worked on, and what the impact was? Is the candidate using buzzwords that sound out of place?
- Appearance: the resume should look professional and simple, minimising flashy graphics as much as possible. Is there attention to detail, e.g. good whitespace and flawless spelling?
- University: universities should be ranked as follows: Oxford/Cambridge, Imperial, Warwick/UCL, other Russell Group, non-Russell Group. Note that some resumes may anonymise their university.
- Miscellaneous: any other observation as you see fit.

You MUST end your response with 'I prefer Resume A' or 'I prefer Resume B'."""

    HAIKU = "claude-3-haiku-20240307"
    SONNET = "claude-3-5-sonnet-20240620"

    def __init__(self, resume_folder, model='sonnet', temperature=0):
        self.resume_folder = resume_folder
        self.model = model
        self.temperature = temperature
        self.client = anthropic.Anthropic()

        self.num_calls = {'haiku': 0, 'sonnet': 0}

        self.should_swap_mediatype = False

    def get_image_data(self, ranked: bool, image_filename):
        path = f'./{self.resume_folder}/{'ranked' if ranked else 'unranked'}/{image_filename}' # e.g. ./unranked/CV.png

        with open(path, 'rb') as image_file:
            return base64.b64encode(image_file.read()).decode('utf-8')
        
    def construct_resumes_dict(self, unranked_filename, ranked_filename):
        ranked_data = self.get_image_data(ranked=True, image_filename=ranked_filename)
        unranked_data = self.get_image_data(ranked=False, image_filename=unranked_filename)

        # Are the images jpg or png
        get_image_type = lambda image_filename: 'jpeg' if image_filename.split('.')[1] == 'jpg' else 'png'
        ranked_type, unranked_type = get_image_type(ranked_filename), get_image_type(unranked_filename)

        # Construct dictionary containing the two resumes
        resumes = {'Resume A': {}, 'Resume B': {}}
        self.to_be_ranked_is_A = False
        resumes['Resume A']['filename'] = ranked_filename
        resumes['Resume A']['data'] = ranked_data
        resumes['Resume A']['type'] = ranked_type
        resumes['Resume B']['filename'] = unranked_filename
        resumes['Resume B']['data'] = unranked_data
        resumes['Resume B']['type'] = unranked_type

        self.current_resumes = resumes

    def randomise_resumes(self):
        rand_int = randint(0, 1)
        # if rand_int is 1 swap resume A and B  
        if rand_int:
            temp = self.current_resumes['Resume A']
            self.current_resumes['Resume A'] = self.current_resumes['Resume B']
            self.current_resumes['Resume B'] = temp
            self.to_be_ranked_is_A = not self.to_be_ranked_is_A

    def compare_resumes_with_llm(self):
        # Update num_calls
        self.num_calls[self.model] += 1

        self.randomise_resumes()

        # print(f'name={self.current_resumes['Resume A']['filename']}, type={self.current_resumes['Resume A']['type']}')
        # print(f'name={self.current_resumes['Resume B']['filename']}, type={self.current_resumes['Resume B']['type']}')

        mediatype_A = f"image/{self.current_resumes['Resume A']['type']}"
        mediatype_B = f"image/{self.current_resumes['Resume B']['type']}"

        print("Comparing resumes...")

        def call_claude():
            print(f'{mediatype_A=}, {mediatype_A=}')
            print(f'{self.current_resumes['Resume A']['filename']=}')

            return self.client.messages.create(
            model = self.SONNET if self.model == 'sonnet' else self.HAIKU,
            max_tokens=2000,
            temperature=self.temperature,
            messages=[
                {

                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": "Resume A:"
                        },
                        {
                            "type": "image",
                            "source": {
                                "type": "base64",
                                "media_type": mediatype_A,
                                "data": self.current_resumes['Resume A']['data']
                            }
                        },
                        {
                            "type": "text",
                            "text": "Resume B:"
                        },
                        {
                            "type": "image",
                            "source": {
                                "type": "base64",
                                "media_type": mediatype_B,
                                "data": self.current_resumes['Resume B']['data']
                            }
                        },
                        {
                            "type": "text",
                            "text": self.PROMPT
                        }
                    ]
                }
            ]
        )

        try:
            self.should_swap_mediatype = False
            message = call_claude()
        except:
            # Error is most likely because mediatype was wrong
            if self.to_be_ranked_is_A:
                # Switch jpeg to png or vice versa
                mediatype_A = 'image/jpeg' if mediatype_A == 'image/png' else 'image/png'
            else:
                mediatype_B = 'image/jpeg' if mediatype_B == 'image/png' else 'image/png'

            print(f'downstairs: {mediatype_A=}, {mediatype_B=}')

            # Signal that rename is required
            self.should_swap_mediatype = True

            # Retry
            message = call_claude()
        
        if 'prefer resume a' in message.content[0].text.lower():
            winner = 'Resume A'
        elif 'prefer resume b' in message.content[0].text.lower():
            winner = 'Resume B'
        else:
            winner = None
            print("WARNING: Claude did not state winner")
            print('here is what it said:')
            print(message.content[0].text)
            input('Press Any Key To Continue')
        
        return {'Resume A': self.current_resumes['Resume A']['filename'],
                 'Resume B': self.current_resumes['Resume B']['filename'],
                 'winner': winner, # "Resume A" or "Resume B"
                 'to_be_ranked_resume': 'Resume A' if self.to_be_ranked_is_A else 'Resume B',
                 'claude_response': message.content[0].text}

    @staticmethod
    def pretty_print(comparison):
        """Pretty prints comparison dictionary."""
        for key, value in comparison.items():
            if key == 'claude_response':
                print(f'Claude:\n{value}')
            else:
                print(f'{key}: {value}')
    
    def best_of_n(self, n, unranked_filename, ranked_filename):
        """Make LLM compare resumes best-of-n style.
        The return format is identical to a regular comparison for now."""
        if n % 2 == 0:
            raise ValueError('n must be odd for best of n')
        wins_required = (n + 1) // 2

        print(f"Starting best of {n} comparison")

        self.construct_resumes_dict(unranked_filename, ranked_filename)

        to_be_ranked_wins, to_be_ranked_losses = 0, 0

        # Store one comparison where to_be_ranked wins, one where it loses
        win_comparison, loss_comparison = None, None
        
        for _ in range(n):
            comparison = self.compare_resumes_with_llm()
            if comparison['to_be_ranked_resume'] == comparison['winner']:
                to_be_ranked_wins += 1
                win_comparison = comparison
            else:
                to_be_ranked_losses += 1
                loss_comparison = comparison

            self.pretty_print(comparison)

            if to_be_ranked_wins == wins_required:
                print(f'Win; wins={to_be_ranked_wins}, losses={to_be_ranked_losses}')
                return win_comparison
            
            if to_be_ranked_losses == wins_required:
                print(f'Loss; wins={to_be_ranked_wins}, losses={to_be_ranked_losses}')
                return loss_comparison

    def main(self, unranked_filename, ranked_filename):
        self.construct_resumes_dict(unranked_filename, ranked_filename)
        return self.compare_resumes_with_llm()
    
if __name__ == "__main__":
    resume_comparer = LLMResumeComparer(resume_folder='test_resumes', model='sonnet', temperature=0)
    comparison = resume_comparer.best_of_n(3, '000-aaaresume2.png', '001-resume_test_update.jpg')

"""
BACKLOG

- write a function that pretty-prints a `comparison` dictionary (ideally make a `Comparison` object)
- modify best of n comparison so that it accepts an initial value for wins / losses
- create timers + api cost calculators
"""
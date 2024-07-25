import anthropic
import base64
from random import randint

class LLMResumeComparer:
    PROMPT = """You are an expert software engineering recruiter tasked with comparing two resumes for an early-career software engineering position. Your goal is to analyze both resumes thoroughly and determine which candidate would be a better fit for the role.

Please follow these steps:

1. Carefully review both resumes, paying attention to education, work experience, projects, technical skills, and any other relevant information.

2. For each resume, list the key strengths and potential weaknesses or areas of concern.

3. Compare the resumes based on the following criteria:
   - Relevance and and amount of work experience
   - Depth and breadth of technical skills
   - Education and academic performance
   - Project experience and its relevance to software engineering
   - Evidence of problem-solving abilities and initiative
   - Any unique qualities or experiences that stand out

4. Furthermore, the following are negative criteria, which should be discarded or treated as less relevant factors:
   - IGNORE Certifications, such as those from Coursera or other MOOCs.
   - IGNORE Leadership roles and extracurricular activities.
   - IGNORE Grades from before university (highschool grades).
   - IGNORE How far into the degree the candidate is; it doesn't matter if they are a graduate, near graduation or still a few years away from graduation.

5. Consider how well each candidate's background aligns with typical requirements for an early-career software engineering role.

6. Weigh the pros and cons of each resume, considering which candidate is likely to perform better in the role and have more potential for growth.

7. After thorough analysis and comparison, form your conclusion about which resume you prefer.

8. Explain your reasoning in detail, covering all the points you considered in your decision-making process.

9. Only after providing your complete analysis and reasoning, state your final decision by writing either "I prefer Resume A" or "I prefer Resume B" as the very last line of your response.

Remember, your goal is to provide a comprehensive comparison and justification for your choice before stating your final preference."""

    HAIKU = "claude-3-haiku-20240307"
    SONNET = "claude-3-5-sonnet-20240620"

    def __init__(self, resume_folder, model='sonnet', temperature=0):
        self.resume_folder = resume_folder
        self.model = model
        self.temperature = temperature
        self.client = anthropic.Anthropic()

        self.num_calls = {'haiku': 0, 'sonnet': 0}

        self.should_swap_mediatype = False

    def get_image_data(self, image_filename):
        path = f'{self.resume_folder}/ranked/{image_filename}'

        with open(path, 'rb') as image_file:
            return base64.b64encode(image_file.read()).decode('utf-8')
        
    def construct_resumes_dict(self, resume1, resume2):
        data1 = self.get_image_data(image_filename=resume1)
        data2 = self.get_image_data(image_filename=resume2)

        # Are the images jpg or png
        get_image_type = lambda image_filename: 'jpeg' if image_filename.split('.')[1] == 'jpg' else 'png'
        image_type1, image_type2 = get_image_type(resume1), get_image_type(resume2)

        # Construct dictionary containing the two resumes
        resumes = {'Resume A': {}, 'Resume B': {}}
        self.A_is_1 = True
        resumes['Resume A']['filename'] = resume1
        resumes['Resume A']['data'] = data1
        resumes['Resume A']['type'] = image_type1
        resumes['Resume B']['filename'] = resume2
        resumes['Resume B']['data'] = data2
        resumes['Resume B']['type'] = image_type2

        self.current_resumes = resumes

    def randomise_resumes(self):
        rand_int = randint(0, 1)
        # if rand_int is 1 swap resume A and B  
        if rand_int:
            temp = self.current_resumes['Resume A']
            self.current_resumes['Resume A'] = self.current_resumes['Resume B']
            self.current_resumes['Resume B'] = temp
            self.A_is_1 = not self.A_is_1

    def compare_resumes_with_llm(self):
        # Update num_calls
        self.num_calls[self.model] += 1

        self.randomise_resumes()

        mediatype_A = f"image/{self.current_resumes['Resume A']['type']}"
        mediatype_B = f"image/{self.current_resumes['Resume B']['type']}"

        print("Comparing resumes...")

        def call_claude():
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
            if self.A_is_1:
                # Switch jpeg to png or vice versa
                mediatype_A = 'image/jpeg' if mediatype_A == 'image/png' else 'image/png'
            else:
                mediatype_B = 'image/jpeg' if mediatype_B == 'image/png' else 'image/png'

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
                 'resume1': 'Resume A' if self.A_is_1 else 'Resume B',
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

    def compare_resumes(self, resume1, resume2):
        self.construct_resumes_dict(resume1, resume2)
        return self.compare_resumes_with_llm()
    
if __name__ == "__main__":
    resume_comparer = LLMResumeComparer(resume_folder='test_resumes', model='sonnet', temperature=0)
    comparison = resume_comparer.best_of_n(1, '000-jorge.png', '001-resume_test_update.jpg')

"""
BACKLOG

- write a function that pretty-prints a `comparison` dictionary (ideally make a `Comparison` object)
- modify best of n comparison so that it accepts an initial value for wins / losses
- create timers + api cost calculators
"""